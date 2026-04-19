"""
BE-API: Positive signed-route coverage using client_raw.

Verifies that high-risk mutation endpoints accept properly signed requests
using real device registration — no signing bypass (client_raw fixture).

Covered routes:
  POST /api/v1/orders
  POST /api/v1/candidates/{id}/documents/upload
  POST /api/v1/attendance/exceptions
  POST /api/v1/orders/{id}/bargaining/offer
  POST /api/v1/auth/password/change
  POST /api/v1/orders/{id}/payment/proof
  POST /api/v1/attendance/exceptions/{id}/proof
"""
from __future__ import annotations

import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .conftest import login


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _keypair():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv, pub_pem


def _signing_headers(priv, method: str, path: str, body_bytes: bytes, device_id: str) -> dict:
    """Build X-Timestamp, X-Nonce, X-Device-ID, X-Request-Signature for one request."""
    timestamp = _now_iso()
    nonce = f"n-{uuid.uuid4().hex}"
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    canonical = (
        "\n".join([method.upper(), path, timestamp, nonce, device_id, body_hash]) + "\n"
    )
    sig = base64.b64encode(
        priv.sign(canonical.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    ).decode()
    return {
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Device-ID": device_id,
        "X-Request-Signature": sig,
    }


def _build_multipart(file_bytes: bytes, filename: str) -> tuple[bytes, str]:
    """Return (body_bytes, content_type) for a minimal single-file multipart form."""
    boundary = b"sigtest" + uuid.uuid4().hex[:12].encode()
    body = (
        b"--" + boundary + b"\r\n"
        + f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        + b"Content-Type: application/pdf\r\n"
        + b"\r\n"
        + file_bytes
        + b"\r\n--" + boundary + b"--\r\n"
    )
    content_type = f"multipart/form-data; boundary={boundary.decode()}"
    return body, content_type


async def _register_device(client, auth_headers: dict):
    """Register a device (no signing required) and return (device_id_str, priv_key)."""
    priv, pub_pem = _keypair()
    fingerprint = f"fp-{uuid.uuid4().hex[:16]}"
    resp = await client.post(
        "/api/v1/auth/device/register",
        headers=auth_headers,
        json={"device_fingerprint": fingerprint, "public_key_pem": pub_pem, "label": "test"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["device_id"], priv


async def _create_candidate_profile(client, reviewer_token: str, candidate_user_id) -> str:
    resp = await client.post(
        "/api/v1/candidates",
        params={"user_id": str(candidate_user_id)},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_service_item(test_session_factory, bargaining: bool = False) -> uuid.UUID:
    from src.persistence.models.order import ServiceItem

    async with test_session_factory() as session:
        item = ServiceItem(
            item_code=f"SVC-{uuid.uuid4().hex[:6].upper()}",
            name="Signing Test Service",
            pricing_mode="bargaining" if bargaining else "fixed",
            fixed_price=Decimal("150.00") if not bargaining else None,
            is_capacity_limited=False,
            bargaining_enabled=bargaining,
            is_active=True,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item.id


async def _insert_order(test_session_factory, candidate_profile_id: str, item_id: uuid.UUID) -> str:
    """Insert a pending_payment bargaining order directly — avoids needing a second signed call."""
    from src.persistence.models.order import Order

    async with test_session_factory() as session:
        order = Order(
            candidate_id=uuid.UUID(candidate_profile_id),
            item_id=item_id,
            status="pending_payment",
            pricing_mode="bargaining",
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return str(order.id)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signed_create_order_succeeds(
    client_raw, seeded_user, seeded_reviewer, test_session_factory
):
    """POST /api/v1/orders — real ECDSA signing → 201."""
    rev_token = await login(client_raw, seeded_reviewer)
    await _create_candidate_profile(client_raw, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client_raw, seeded_user)
    auth = {"Authorization": f"Bearer {cand_token}"}
    device_id, priv = await _register_device(client_raw, auth)

    body_dict = {"item_id": str(item_id), "pricing_mode": "fixed"}
    body_bytes = json.dumps(body_dict, separators=(",", ":")).encode()
    sign_hdrs = _signing_headers(priv, "POST", "/api/v1/orders", body_bytes, device_id)

    resp = await client_raw.post(
        "/api/v1/orders",
        headers={**auth, **sign_hdrs, "Content-Type": "application/json"},
        content=body_bytes,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["status"] == "pending_payment"


@pytest.mark.asyncio
async def test_signed_document_upload_succeeds(
    client_raw, seeded_user, seeded_reviewer, test_session_factory, tmp_file_store
):
    """POST /api/v1/candidates/{id}/documents/upload — real ECDSA signing with multipart → 201."""
    rev_token = await login(client_raw, seeded_reviewer)
    cand_profile_id = await _create_candidate_profile(client_raw, rev_token, seeded_user["id"])

    cand_token = await login(client_raw, seeded_user)
    auth = {"Authorization": f"Bearer {cand_token}"}
    device_id, priv = await _register_device(client_raw, auth)

    path = f"/api/v1/candidates/{cand_profile_id}/documents/upload"
    file_bytes = b"%PDF-1.4 signed-route-test"
    body_bytes, content_type = _build_multipart(file_bytes, "test.pdf")
    sign_hdrs = _signing_headers(priv, "POST", path, body_bytes, device_id)

    resp = await client_raw.post(
        path,
        headers={**auth, **sign_hdrs, "Content-Type": content_type},
        content=body_bytes,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["original_filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_signed_attendance_exception_succeeds(
    client_raw, seeded_user, seeded_reviewer, test_session_factory, tmp_file_store
):
    """POST /api/v1/attendance/exceptions — real ECDSA signing → 201."""
    rev_token = await login(client_raw, seeded_reviewer)
    await _create_candidate_profile(client_raw, rev_token, seeded_user["id"])

    cand_token = await login(client_raw, seeded_user)
    auth = {"Authorization": f"Bearer {cand_token}"}
    device_id, priv = await _register_device(client_raw, auth)

    body_dict = {"candidate_statement": "I was ill on that day."}
    body_bytes = json.dumps(body_dict, separators=(",", ":")).encode()
    path = "/api/v1/attendance/exceptions"
    sign_hdrs = _signing_headers(priv, "POST", path, body_bytes, device_id)

    resp = await client_raw.post(
        path,
        headers={**auth, **sign_hdrs, "Content-Type": "application/json"},
        content=body_bytes,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["status"] == "pending_review"


@pytest.mark.asyncio
async def test_signed_bargaining_offer_succeeds(
    client_raw, seeded_user, seeded_reviewer, test_session_factory
):
    """POST /api/v1/orders/{id}/bargaining/offer — real ECDSA signing → 201."""
    rev_token = await login(client_raw, seeded_reviewer)
    cand_profile_id = await _create_candidate_profile(client_raw, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory, bargaining=True)
    order_id = await _insert_order(test_session_factory, cand_profile_id, item_id)

    cand_token = await login(client_raw, seeded_user)
    auth = {"Authorization": f"Bearer {cand_token}"}
    device_id, priv = await _register_device(client_raw, auth)

    path = f"/api/v1/orders/{order_id}/bargaining/offer"
    nonce = f"n-{uuid.uuid4().hex}"
    body_dict = {"amount": "120.00", "nonce": nonce, "timestamp": _now_iso()}
    body_bytes = json.dumps(body_dict, separators=(",", ":")).encode()
    sign_hdrs = _signing_headers(priv, "POST", path, body_bytes, device_id)

    resp = await client_raw.post(
        path,
        headers={**auth, **sign_hdrs, "Content-Type": "application/json"},
        content=body_bytes,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["offer_number"] == 1


@pytest.mark.asyncio
async def test_signed_password_change_succeeds(
    client_raw, seeded_user
):
    """POST /api/v1/auth/password/change — real ECDSA signing → 200."""
    token = await login(client_raw, seeded_user)
    auth = {"Authorization": f"Bearer {token}"}
    device_id, priv = await _register_device(client_raw, auth)

    path = "/api/v1/auth/password/change"
    nonce = f"n-{uuid.uuid4().hex}"
    body_dict = {
        "current_password": seeded_user["password"],
        "new_password": "N3wSecurePassw0rd!",
        "nonce": nonce,
        "timestamp": _now_iso(),
    }
    body_bytes = json.dumps(body_dict, separators=(",", ":")).encode()
    sign_hdrs = _signing_headers(priv, "POST", path, body_bytes, device_id)

    resp = await client_raw.post(
        path,
        headers={**auth, **sign_hdrs, "Content-Type": "application/json"},
        content=body_bytes,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["password_changed"] is True


@pytest.mark.asyncio
async def test_signed_payment_proof_submission_succeeds(
    client_raw, seeded_user, seeded_reviewer, test_session_factory
):
    """POST /api/v1/orders/{id}/payment/proof — full flow through client_raw (no bypass)."""
    rev_token = await login(client_raw, seeded_reviewer)
    await _create_candidate_profile(client_raw, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client_raw, seeded_user)
    auth = {"Authorization": f"Bearer {cand_token}"}
    device_id, priv = await _register_device(client_raw, auth)

    # Create order with real signing
    body_dict = {"item_id": str(item_id), "pricing_mode": "fixed"}
    body_bytes = json.dumps(body_dict, separators=(",", ":")).encode()
    sign_hdrs = _signing_headers(priv, "POST", "/api/v1/orders", body_bytes, device_id)
    order_resp = await client_raw.post(
        "/api/v1/orders",
        headers={**auth, **sign_hdrs, "Content-Type": "application/json"},
        content=body_bytes,
    )
    assert order_resp.status_code == 201, order_resp.text
    order_id = order_resp.json()["data"]["id"]

    # Submit payment proof — also signed after audit-5 B2.
    proof_path = f"/api/v1/orders/{order_id}/payment/proof"
    proof_body = json.dumps(
        {"amount": "150.00", "payment_method": "bank_transfer", "reference_number": "REF-SIGTEST-001"},
        separators=(",", ":"),
    ).encode()
    proof_sign_hdrs = _signing_headers(priv, "POST", proof_path, proof_body, device_id)
    proof_resp = await client_raw.post(
        proof_path,
        headers={**auth, **proof_sign_hdrs, "Content-Type": "application/json"},
        content=proof_body,
    )
    assert proof_resp.status_code == 200, proof_resp.text
    assert proof_resp.json()["data"]["payment_method"] == "bank_transfer"


@pytest.mark.asyncio
async def test_signed_attendance_proof_upload_succeeds(
    client_raw, seeded_user, seeded_reviewer, test_session_factory, tmp_file_store
):
    """POST /api/v1/attendance/exceptions/{id}/proof — full flow through client_raw (no bypass)."""
    rev_token = await login(client_raw, seeded_reviewer)
    await _create_candidate_profile(client_raw, rev_token, seeded_user["id"])

    cand_token = await login(client_raw, seeded_user)
    auth = {"Authorization": f"Bearer {cand_token}"}
    device_id, priv = await _register_device(client_raw, auth)

    # Create attendance exception with real signing
    exc_path = "/api/v1/attendance/exceptions"
    exc_body = json.dumps(
        {"candidate_statement": "Medical emergency prevented attendance."},
        separators=(",", ":"),
    ).encode()
    sign_hdrs = _signing_headers(priv, "POST", exc_path, exc_body, device_id)
    exc_resp = await client_raw.post(
        exc_path,
        headers={**auth, **sign_hdrs, "Content-Type": "application/json"},
        content=exc_body,
    )
    assert exc_resp.status_code == 201, exc_resp.text
    exception_id = exc_resp.json()["data"]["id"]

    # Upload proof file — also signed after audit-5 B2.
    proof_path = f"/api/v1/attendance/exceptions/{exception_id}/proof"
    file_bytes = b"%PDF-1.4 proof-upload-sigtest"
    body_bytes, content_type = _build_multipart(file_bytes, "proof.pdf")
    proof_sign_hdrs = _signing_headers(priv, "POST", proof_path, body_bytes, device_id)
    proof_resp = await client_raw.post(
        proof_path,
        headers={**auth, **proof_sign_hdrs, "Content-Type": content_type},
        content=body_bytes,
    )
    assert proof_resp.status_code == 201, proof_resp.text
    assert proof_resp.json()["data"]["original_filename"] == "proof.pdf"
