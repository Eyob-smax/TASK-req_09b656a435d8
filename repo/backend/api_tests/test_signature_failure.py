"""
BE-API: signed-route failure modes.

Every signed route must reject:
    * missing/invalid signature headers → SIGNATURE_INVALID
    * stale timestamp → CLOCK_SKEW
    * reused nonce → NONCE_REPLAY

All tests use client_raw (signing enforcement active, not bypassed).
"""
from datetime import datetime, timedelta, timezone
import uuid

import pytest

from .conftest import login


def _now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def _login_raw(client_raw, user):
    resp = await client_raw.post(
        "/api/v1/auth/login",
        json={
            "username": user["username"],
            "password": user["password"],
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": _now(),
        },
    )
    return resp.json()["data"]


@pytest.mark.asyncio
async def test_missing_signature_on_password_change(client_raw, seeded_user):
    """POST /auth/password/change without signing headers → SIGNATURE_INVALID."""
    tokens = await _login_raw(client_raw, seeded_user)
    resp = await client_raw.post(
        "/api/v1/auth/password/change",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={
            "current_password": seeded_user["password"],
            "new_password": "new-correct-horse-battery",
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": _now(),
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_missing_signature_on_order_create(client_raw, seeded_user, seeded_reviewer, test_session_factory):
    """POST /orders without signing headers → SIGNATURE_INVALID."""
    import uuid as _uuid
    from decimal import Decimal
    from src.persistence.models.order import ServiceItem

    async with test_session_factory() as session:
        item = ServiceItem(
            item_code=f"SVC-{_uuid.uuid4().hex[:6].upper()}",
            name="Signing Test Service",
            pricing_mode="fixed",
            fixed_price=Decimal("100.00"),
            is_capacity_limited=False,
            bargaining_enabled=False,
            is_active=True,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        item_id = item.id

    rev_tokens = await _login_raw(client_raw, seeded_reviewer)
    await client_raw.post(
        "/api/v1/candidates",
        params={"user_id": str(seeded_user["id"])},
        headers={"Authorization": f"Bearer {rev_tokens['access_token']}"},
    )

    tokens = await _login_raw(client_raw, seeded_user)
    resp = await client_raw.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"item_id": str(item_id), "pricing_mode": "fixed"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_missing_signature_on_document_upload(client_raw, seeded_user, seeded_reviewer, tmp_file_store):
    """POST /candidates/{id}/documents/upload without signing → SIGNATURE_INVALID."""
    import io

    rev_tokens = await _login_raw(client_raw, seeded_reviewer)
    profile_resp = await client_raw.post(
        "/api/v1/candidates",
        params={"user_id": str(seeded_user["id"])},
        headers={"Authorization": f"Bearer {rev_tokens['access_token']}"},
    )
    assert profile_resp.status_code == 201
    profile_id = profile_resp.json()["data"]["id"]

    tokens = await _login_raw(client_raw, seeded_user)
    pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f\ntrailer<</Root 1 0 R>>\nstartxref\n9\n%%EOF"
    resp = await client_raw.post(
        f"/api/v1/candidates/{profile_id}/documents/upload",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        files={"file": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_missing_signature_on_attendance_exception(client_raw, seeded_user, seeded_reviewer):
    """POST /attendance/exceptions without signing → SIGNATURE_INVALID."""
    rev_tokens = await _login_raw(client_raw, seeded_reviewer)
    await client_raw.post(
        "/api/v1/candidates",
        params={"user_id": str(seeded_user["id"])},
        headers={"Authorization": f"Bearer {rev_tokens['access_token']}"},
    )

    tokens = await _login_raw(client_raw, seeded_user)
    resp = await client_raw.post(
        "/api/v1/attendance/exceptions",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"candidate_statement": "I was ill."},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_missing_signature_on_bargaining_offer(client_raw, seeded_user, seeded_reviewer, test_session_factory):
    """POST /orders/{id}/bargaining/offer without signing → SIGNATURE_INVALID."""
    import uuid as _uuid
    from decimal import Decimal
    from src.persistence.models.order import ServiceItem

    async with test_session_factory() as session:
        item = ServiceItem(
            item_code=f"SVC-{_uuid.uuid4().hex[:6].upper()}",
            name="Bargaining Sign Test",
            pricing_mode="bargaining",
            fixed_price=None,
            is_capacity_limited=False,
            bargaining_enabled=True,
            is_active=True,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        item_id = item.id

    rev_tokens = await _login_raw(client_raw, seeded_reviewer)
    await client_raw.post(
        "/api/v1/candidates",
        params={"user_id": str(seeded_user["id"])},
        headers={"Authorization": f"Bearer {rev_tokens['access_token']}"},
    )

    # Create order via the non-signing client would fail, so we seed it directly
    tokens = await _login_raw(client_raw, seeded_user)
    # Use a dummy order id — we just need to verify signing is checked before business logic
    fake_order_id = str(_uuid.uuid4())
    resp = await client_raw.post(
        f"/api/v1/orders/{fake_order_id}/bargaining/offer",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"amount": "150.00"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_stale_timestamp_on_login_returns_clock_skew(client_raw, seeded_user):
    """Login with stale timestamp → CLOCK_SKEW."""
    stale = (datetime.now(tz=timezone.utc) - timedelta(minutes=5)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    resp = await client_raw.post(
        "/api/v1/auth/login",
        json={
            "username": seeded_user["username"],
            "password": seeded_user["password"],
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": stale,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CLOCK_SKEW"


@pytest.mark.asyncio
async def test_replayed_nonce_returns_nonce_replay(client_raw, seeded_user):
    """Login nonce reuse → NONCE_REPLAY."""
    shared_nonce = f"n-{uuid.uuid4().hex}"
    payload1 = {
        "username": seeded_user["username"],
        "password": seeded_user["password"],
        "nonce": shared_nonce,
        "timestamp": _now(),
    }
    first = await client_raw.post("/api/v1/auth/login", json=payload1)
    assert first.status_code == 200

    payload2 = dict(payload1)
    payload2["timestamp"] = _now()
    second = await client_raw.post("/api/v1/auth/login", json=payload2)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "NONCE_REPLAY"
