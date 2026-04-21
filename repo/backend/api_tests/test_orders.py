"""BE-API: Service catalog, order creation, row scoping, cancel, events, capacity."""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

import json

from .conftest import login, make_signing_headers, register_device, signed_post_json


async def _create_service_item(test_session_factory, *, fixed_price="100.00", capacity_limited=False, total_slots=10):
    from src.persistence.models.order import ServiceItem, ServiceItemInventory

    async with test_session_factory() as session:
        item = ServiceItem(
            item_code=f"SVC-{uuid.uuid4().hex[:6].upper()}",
            name="Test Service",
            pricing_mode="fixed",
            fixed_price=Decimal(fixed_price),
            is_capacity_limited=capacity_limited,
            bargaining_enabled=False,
            is_active=True,
        )
        session.add(item)
        await session.flush()
        if capacity_limited:
            inv = ServiceItemInventory(
                item_id=item.id,
                total_slots=total_slots,
                reserved_count=0,
            )
            session.add(inv)
        await session.commit()
        await session.refresh(item)
        return item.id


async def _create_order(client, cand_token: str, item_id, pricing_mode: str = "fixed") -> str:
    auth = {"Authorization": f"Bearer {cand_token}"}
    device_id, priv = await register_device(client, auth)
    path = "/api/v1/orders"
    body = json.dumps({"item_id": str(item_id), "pricing_mode": pricing_mode}, separators=(",", ":")).encode()
    sign_hdrs = make_signing_headers(priv, "POST", path, body, device_id)
    resp = await client.post(path, headers={**auth, **sign_hdrs, "Content-Type": "application/json"}, content=body)
    return resp


async def _create_candidate_profile(client, reviewer_token: str, candidate_user_id) -> str:
    resp = await client.post(
        "/api/v1/candidates",
        params={"user_id": str(candidate_user_id)},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


@pytest.mark.asyncio
async def test_create_order_fixed_price(client, seeded_user, seeded_reviewer, test_session_factory):
    rev_token = await login(client, seeded_reviewer)
    profile_id = await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    resp = await _create_order(client, cand_token, item_id)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "pending_payment"


@pytest.mark.asyncio
async def test_create_order_idempotency(client, seeded_user, seeded_reviewer, test_session_factory):
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    idem_key = uuid.uuid4().hex

    auth = {"Authorization": f"Bearer {cand_token}", "Idempotency-Key": idem_key}
    device_id, priv = await register_device(client, {"Authorization": f"Bearer {cand_token}"})
    path = "/api/v1/orders"
    body = json.dumps({"item_id": str(item_id), "pricing_mode": "fixed"}, separators=(",", ":")).encode()
    sign_hdrs = make_signing_headers(priv, "POST", path, body, device_id)

    r1 = await client.post(path, headers={**auth, **sign_hdrs, "Content-Type": "application/json"}, content=body)
    assert r1.status_code == 201
    order_id_1 = r1.json()["data"]["id"]

    # Idempotent replay: same device, same body — server deduplicates on idempotency key
    sign_hdrs2 = make_signing_headers(priv, "POST", path, body, device_id)
    r2 = await client.post(path, headers={**auth, **sign_hdrs2, "Content-Type": "application/json"}, content=body)
    assert r2.status_code == 201
    order_id_2 = r2.json()["data"]["id"]

    assert order_id_1 == order_id_2


@pytest.mark.asyncio
async def test_create_order_idempotency_conflict_on_body_change(
    client, seeded_user, seeded_reviewer, test_session_factory
):
    """Same Idempotency-Key with a different request body → 409 IDEMPOTENCY_CONFLICT.

    Enforced at the route layer via IdempotencyStore.fetch in
    src/api/routes/orders.py (see docs/api-spec.md §5).
    """
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_a = await _create_service_item(test_session_factory)
    item_b = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    idem_key = uuid.uuid4().hex

    auth = {"Authorization": f"Bearer {cand_token}", "Idempotency-Key": idem_key}
    device_id, priv = await register_device(client, {"Authorization": f"Bearer {cand_token}"})
    path = "/api/v1/orders"

    body_a = json.dumps({"item_id": str(item_a), "pricing_mode": "fixed"}, separators=(",", ":")).encode()
    sign_hdrs_a = make_signing_headers(priv, "POST", path, body_a, device_id)
    r1 = await client.post(
        path,
        headers={**auth, **sign_hdrs_a, "Content-Type": "application/json"},
        content=body_a,
    )
    assert r1.status_code == 201, r1.text

    body_b = json.dumps({"item_id": str(item_b), "pricing_mode": "fixed"}, separators=(",", ":")).encode()
    sign_hdrs_b = make_signing_headers(priv, "POST", path, body_b, device_id)
    r2 = await client.post(
        path,
        headers={**auth, **sign_hdrs_b, "Content-Type": "application/json"},
        content=body_b,
    )
    assert r2.status_code == 409, r2.text
    assert r2.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


@pytest.mark.asyncio
async def test_create_order_idempotency_row_persisted(
    client, seeded_user, seeded_reviewer, test_session_factory
):
    """After a successful POST /orders with Idempotency-Key, the idempotency_keys
    row must exist keyed (key, "POST", "/api/v1/orders")."""
    from sqlalchemy import select

    from src.persistence.models.idempotency import IdempotencyKey

    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    idem_key = uuid.uuid4().hex

    auth = {"Authorization": f"Bearer {cand_token}", "Idempotency-Key": idem_key}
    device_id, priv = await register_device(client, {"Authorization": f"Bearer {cand_token}"})
    path = "/api/v1/orders"
    body = json.dumps({"item_id": str(item_id), "pricing_mode": "fixed"}, separators=(",", ":")).encode()
    sign_hdrs = make_signing_headers(priv, "POST", path, body, device_id)
    resp = await client.post(
        path,
        headers={**auth, **sign_hdrs, "Content-Type": "application/json"},
        content=body,
    )
    assert resp.status_code == 201, resp.text

    async with test_session_factory() as session:
        row = (
            await session.execute(
                select(IdempotencyKey).where(
                    IdempotencyKey.key == idem_key,
                    IdempotencyKey.method == "POST",
                    IdempotencyKey.path == "/api/v1/orders",
                )
            )
        ).scalar_one_or_none()
    assert row is not None
    assert row.response_status == 201


@pytest.mark.asyncio
async def test_list_orders_candidate_sees_only_owned_orders(
    client, seeded_user, seeded_reviewer, test_session_factory, _install_jwt_keys
):
    from src.persistence.models.auth import User
    from src.security.passwords import hash_password

    rev_token = await login(client, seeded_reviewer)
    item_id = await _create_service_item(test_session_factory)

    async with test_session_factory() as session:
        user_b = User(
            username=f"candidate-b-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("correct horse battery staple"),
            role="candidate",
            full_name="Candidate B",
            is_active=True,
            is_locked=False,
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(user_b)
        user_b_data = {
            "id": user_b.id,
            "username": user_b.username,
            "password": "correct horse battery staple",
        }

    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    await _create_candidate_profile(client, rev_token, user_b_data["id"])

    cand_a_token = await login(client, seeded_user)
    cand_b_token = await login(client, user_b_data)

    order_a_resp = await _create_order(client, cand_a_token, item_id)
    assert order_a_resp.status_code == 201, order_a_resp.text
    order_a_id = order_a_resp.json()["data"]["id"]

    order_b_resp = await _create_order(client, cand_b_token, item_id)
    assert order_b_resp.status_code == 201, order_b_resp.text
    order_b_id = order_b_resp.json()["data"]["id"]

    resp = await client.get(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {cand_a_token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body["data"], list)
    assert "pagination" in body
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["page_size"] == 20
    assert body["pagination"]["total"] == 1
    returned_ids = [order["id"] for order in body["data"]]
    assert order_a_id in returned_ids
    assert order_b_id not in returned_ids


@pytest.mark.asyncio
async def test_order_row_scope(client, seeded_user, seeded_reviewer, test_session_factory, _install_jwt_keys):
    from src.persistence.models.auth import User
    from src.security.passwords import hash_password

    rev_token = await login(client, seeded_reviewer)
    item_id = await _create_service_item(test_session_factory)

    # Create candidate B
    async with test_session_factory() as session:
        user_b = User(
            username=f"bob-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("correct horse battery staple"),
            role="candidate",
            full_name="Bob B",
            is_active=True,
            is_locked=False,
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(user_b)
        user_b_data = {"id": user_b.id, "username": user_b.username, "password": "correct horse battery staple"}

    # Create profiles and orders for both candidates
    profile_a_id = await _create_candidate_profile(client, rev_token, seeded_user["id"])
    profile_b_id = await _create_candidate_profile(client, rev_token, user_b_data["id"])

    token_b = await login(client, user_b_data)
    order_b = await _create_order(client, token_b, item_id)
    assert order_b.status_code == 201
    order_b_id = order_b.json()["data"]["id"]

    # Candidate A tries to read candidate B's order → 403
    token_a = await login(client, seeded_user)
    resp = await client.get(
        f"/api/v1/orders/{order_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cancel_order(client, seeded_user, seeded_reviewer, test_session_factory):
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    order_resp = await _create_order(client, cand_token, item_id)
    assert order_resp.status_code == 201
    order_id = order_resp.json()["data"]["id"]

    cancel_resp = await signed_post_json(
        client, cand_token,
        f"/api/v1/orders/{order_id}/cancel",
        {"notes": "Changed my mind"},
    )
    assert cancel_resp.status_code == 200, cancel_resp.text
    assert cancel_resp.json()["data"]["status"] == "canceled"


@pytest.mark.asyncio
async def test_order_history_records_events(client, seeded_user, seeded_reviewer, test_session_factory):
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    order_resp = await _create_order(client, cand_token, item_id)
    assert order_resp.status_code == 201
    order_id = order_resp.json()["data"]["id"]

    get_resp = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert get_resp.status_code == 200
    events = get_resp.json()["data"]["events"]
    assert len(events) >= 1
    assert events[0]["sequence_number"] == 1


@pytest.mark.asyncio
async def test_list_service_items(client, seeded_user, test_session_factory):
    """GET /api/v1/services — authed users see the active catalog."""
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    resp = await client.get(
        "/api/v1/services",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    ids = [item["id"] for item in body["data"]]
    assert len(body["data"]) >= 1
    assert str(item_id) in ids


@pytest.mark.asyncio
async def test_create_order_no_capacity(client, seeded_user, seeded_reviewer, test_session_factory):
    """Capacity-limited item with 0 available slots → 409 BUSINESS_RULE_VIOLATION."""
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(
        test_session_factory, capacity_limited=True, total_slots=0
    )

    cand_token = await login(client, seeded_user)
    resp = await _create_order(client, cand_token, item_id)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
