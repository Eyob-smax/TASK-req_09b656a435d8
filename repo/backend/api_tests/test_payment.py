"""BE-API: Payment proof, confirm, bargaining offers, accept, counter."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from .conftest import (
    login,
    make_signing_headers,
    register_device,
    signed_post_json,
)


async def _create_service_item(test_session_factory, bargaining=False, fixed_price="200.00"):
    from src.persistence.models.order import ServiceItem

    async with test_session_factory() as session:
        item = ServiceItem(
            item_code=f"SVC-{uuid.uuid4().hex[:6].upper()}",
            name="Payment Test Service",
            pricing_mode="bargaining" if bargaining else "fixed",
            fixed_price=Decimal(fixed_price) if not bargaining else None,
            is_capacity_limited=False,
            bargaining_enabled=bargaining,
            is_active=True,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item.id


async def _create_candidate_profile(client, reviewer_token: str, candidate_user_id) -> str:
    resp = await client.post(
        "/api/v1/candidates",
        params={"user_id": str(candidate_user_id)},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_order(client, cand_token: str, item_id: uuid.UUID, pricing_mode="fixed") -> str:
    auth = {"Authorization": f"Bearer {cand_token}"}
    device_id, priv = await register_device(client, auth)
    path = "/api/v1/orders"
    body = json.dumps({"item_id": str(item_id), "pricing_mode": pricing_mode}, separators=(",", ":")).encode()
    sign_hdrs = make_signing_headers(priv, "POST", path, body, device_id)
    resp = await client.post(path, headers={**auth, **sign_hdrs, "Content-Type": "application/json"}, content=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _submit_offer(client, cand_token: str, order_id: str, amount: str = "150.00"):
    """Submit a bargaining offer with proper ECDSA signing. Returns the response."""
    auth = {"Authorization": f"Bearer {cand_token}"}
    device_id, priv = await register_device(client, auth)
    path = f"/api/v1/orders/{order_id}/bargaining/offer"
    body = json.dumps(
        {"amount": amount, "nonce": f"n-{uuid.uuid4().hex}", "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
        separators=(",", ":"),
    ).encode()
    sign_hdrs = make_signing_headers(priv, "POST", path, body, device_id)
    return await client.post(path, headers={**auth, **sign_hdrs, "Content-Type": "application/json"}, content=body)


@pytest.mark.asyncio
async def test_submit_proof(client, seeded_user, seeded_reviewer, test_session_factory):
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_token, item_id)

    resp = await signed_post_json(
        client, cand_token, f"/api/v1/orders/{order_id}/payment/proof",
        {
            "amount": "200.00",
            "payment_method": "bank_transfer",
            "reference_number": "REF123456",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["confirmed"] is False


@pytest.mark.asyncio
async def test_submit_proof_duplicate(client, seeded_user, seeded_reviewer, test_session_factory):
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_token, item_id)

    payload = {"amount": "200.00", "payment_method": "bank_transfer", "reference_number": "REF1"}
    r1 = await signed_post_json(client, cand_token, f"/api/v1/orders/{order_id}/payment/proof", payload)
    assert r1.status_code == 200, r1.text

    r2 = await signed_post_json(client, cand_token, f"/api/v1/orders/{order_id}/payment/proof", payload)
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


@pytest.mark.asyncio
async def test_confirm_payment_transitions_order(client, seeded_user, seeded_reviewer, test_session_factory):
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory)

    cand_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_token, item_id)

    # Submit proof (signed)
    await signed_post_json(
        client, cand_token, f"/api/v1/orders/{order_id}/payment/proof",
        {"amount": "200.00", "payment_method": "bank_transfer"},
    )

    # Confirm payment as reviewer (signed)
    confirm_resp = await signed_post_json(
        client, rev_token, f"/api/v1/orders/{order_id}/payment/confirm",
        {"amount": "200.00", "payment_method": "bank_transfer"},
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    assert confirm_resp.json()["data"]["status"] == "pending_fulfillment"


@pytest.mark.asyncio
async def test_bargaining_offer_submit(client, seeded_user, seeded_reviewer, test_session_factory):
    """Candidate submits first bargaining offer → 201 with correct offer details."""
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory, bargaining=True)

    cand_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_token, item_id, pricing_mode="bargaining")

    offer_resp = await _submit_offer(client, cand_token, order_id, "150.00")
    assert offer_resp.status_code == 201, offer_resp.text
    offer_body = offer_resp.json()
    assert offer_body["success"] is True
    assert offer_body["data"]["offer_number"] == 1

    # Verify the thread reflects the submitted offer
    thread_resp = await client.get(
        f"/api/v1/orders/{order_id}/bargaining",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert thread_resp.status_code == 200
    body = thread_resp.json()
    assert body["success"] is True
    assert "id" in body["data"]


@pytest.mark.asyncio
async def test_bargaining_offer_limit(client, seeded_user, seeded_reviewer, test_session_factory):
    """4th offer on a bargaining order → 409 BUSINESS_RULE_VIOLATION (max 3 offers)."""
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory, bargaining=True)

    cand_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_token, item_id, pricing_mode="bargaining")

    for _ in range(3):
        r = await _submit_offer(client, cand_token, order_id)
        assert r.status_code == 201, r.text

    r4 = await _submit_offer(client, cand_token, order_id)
    assert r4.status_code == 409
    assert r4.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


@pytest.mark.asyncio
async def test_bargaining_accept_sets_agreed_price(client, seeded_user, seeded_reviewer, test_session_factory):
    """Reviewer accepts offer → thread status 'accepted', agreed_price set, order stays in pending_payment."""
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory, bargaining=True)

    cand_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_token, item_id, pricing_mode="bargaining")

    offer_resp = await _submit_offer(client, cand_token, order_id, "150.00")
    assert offer_resp.status_code == 201, offer_resp.text
    offer_id = offer_resp.json()["data"]["id"]

    accept_resp = await signed_post_json(
        client, rev_token,
        f"/api/v1/orders/{order_id}/bargaining/accept",
        {
            "offer_id": offer_id,
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    assert accept_resp.status_code == 200, accept_resp.text
    assert accept_resp.json()["data"]["status"] == "accepted"

    # Order stays in pending_payment; candidate must still submit payment proof at agreed price
    order_resp = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert order_resp.status_code == 200
    assert order_resp.json()["data"]["status"] == "pending_payment"
    assert order_resp.json()["data"]["agreed_price"] == "150.00"


@pytest.mark.asyncio
async def test_bargaining_counter(client, seeded_user, seeded_reviewer, test_session_factory):
    """Reviewer can counter once via HTTP; second counter attempt → 409 BUSINESS_RULE_VIOLATION."""
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory, bargaining=True)

    cand_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_token, item_id, pricing_mode="bargaining")

    await _submit_offer(client, cand_token, order_id, "150.00")

    r1 = await signed_post_json(
        client, rev_token,
        f"/api/v1/orders/{order_id}/bargaining/counter",
        {"counter_amount": "175.00"},
    )
    assert r1.status_code == 200, r1.text

    r2 = await signed_post_json(
        client, rev_token,
        f"/api/v1/orders/{order_id}/bargaining/counter",
        {"counter_amount": "180.00"},
    )
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


@pytest.mark.asyncio
async def test_bargaining_accept_counter_succeeds(client, seeded_user, seeded_reviewer, test_session_factory):
    """Candidate accepts reviewer counter-offer → thread reaches counter_accepted status."""
    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory, bargaining=True)

    cand_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_token, item_id, pricing_mode="bargaining")

    # Candidate submits offer
    await _submit_offer(client, cand_token, order_id, "130.00")

    # Reviewer counters
    await signed_post_json(
        client, rev_token,
        f"/api/v1/orders/{order_id}/bargaining/counter",
        {"counter_amount": "145.00"},
    )

    # Candidate accepts counter
    resp = await signed_post_json(
        client, cand_token,
        f"/api/v1/orders/{order_id}/bargaining/accept-counter",
        {
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["status"] == "counter_accepted"


@pytest.mark.asyncio
async def test_bargaining_window_expiry(client, seeded_user, seeded_reviewer, test_session_factory):
    """Offer submitted after bargaining window expiry → 409 BUSINESS_RULE_VIOLATION."""
    from datetime import timedelta
    from src.persistence.models.order import BargainingThread

    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    item_id = await _create_service_item(test_session_factory, bargaining=True)

    cand_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_token, item_id, pricing_mode="bargaining")

    now = datetime.now(timezone.utc)
    old_start = now - timedelta(hours=49)
    async with test_session_factory() as session:
        thread = BargainingThread(
            order_id=uuid.UUID(order_id),
            status="open",
            window_starts_at=old_start,
            window_expires_at=old_start + timedelta(hours=48),
            counter_count=0,
        )
        session.add(thread)
        await session.commit()

    resp = await _submit_offer(client, cand_token, order_id, "150.00")
    assert resp.status_code == 409, resp.text
    assert resp.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


@pytest.mark.asyncio
async def test_get_voucher_cross_user_forbidden(
    client, seeded_user, seeded_reviewer, _install_jwt_keys, test_session_factory
):
    """Candidate B cannot read the voucher for Candidate A's order → 403."""
    from src.persistence.models.auth import User
    from src.security.passwords import hash_password

    async with test_session_factory() as session:
        user_b = User(
            username=f"b-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("correct horse battery staple"),
            role="candidate",
            full_name="B Candidate",
            is_active=True,
            is_locked=False,
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(user_b)
        user_b_data = {"id": user_b.id, "username": user_b.username, "password": "correct horse battery staple"}

    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    await _create_candidate_profile(client, rev_token, user_b_data["id"])

    item_id = await _create_service_item(test_session_factory)
    cand_a_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_a_token, item_id)

    # Reviewer issues voucher for candidate A's order (all signed after audit-5 B2)
    await signed_post_json(
        client, cand_a_token, f"/api/v1/orders/{order_id}/payment/proof",
        {"amount": "200.00", "payment_method": "bank_transfer", "reference_number": "REF1"},
    )
    await signed_post_json(
        client, rev_token, f"/api/v1/orders/{order_id}/payment/confirm",
        {"amount": "200.00", "payment_method": "bank_transfer"},
    )
    await signed_post_json(
        client, rev_token, f"/api/v1/orders/{order_id}/voucher",
        {"notes": "Test voucher"},
    )

    # Candidate B tries to read voucher → 403
    cand_b_token = await login(client, user_b_data)
    resp = await client.get(
        f"/api/v1/orders/{order_id}/voucher",
        headers={"Authorization": f"Bearer {cand_b_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_milestones_cross_user_forbidden(
    client, seeded_user, seeded_reviewer, _install_jwt_keys, test_session_factory
):
    """Candidate B cannot list milestones for Candidate A's order → 403."""
    from src.persistence.models.auth import User
    from src.security.passwords import hash_password

    async with test_session_factory() as session:
        user_b = User(
            username=f"b-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("correct horse battery staple"),
            role="candidate",
            full_name="B Candidate",
            is_active=True,
            is_locked=False,
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(user_b)
        user_b_data = {"id": user_b.id, "username": user_b.username, "password": "correct horse battery staple"}

    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    await _create_candidate_profile(client, rev_token, user_b_data["id"])

    item_id = await _create_service_item(test_session_factory)
    cand_a_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_a_token, item_id)

    # Candidate B tries to list milestones for candidate A's order → 403
    cand_b_token = await login(client, user_b_data)
    resp = await client.get(
        f"/api/v1/orders/{order_id}/milestones",
        headers={"Authorization": f"Bearer {cand_b_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_submit_proof_cross_user_forbidden(
    client, seeded_user, seeded_reviewer, _install_jwt_keys, test_session_factory
):
    """Candidate B cannot submit payment proof on Candidate A's order → 403."""
    from src.persistence.models.auth import User
    from src.security.passwords import hash_password

    async with test_session_factory() as session:
        user_b = User(
            username=f"b-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("correct horse battery staple"),
            role="candidate",
            full_name="B Candidate",
            is_active=True,
            is_locked=False,
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(user_b)
        user_b_data = {"id": user_b.id, "username": user_b.username, "password": "correct horse battery staple"}

    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    await _create_candidate_profile(client, rev_token, user_b_data["id"])

    item_id = await _create_service_item(test_session_factory)
    cand_a_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_a_token, item_id)

    cand_b_token = await login(client, user_b_data)
    resp = await signed_post_json(
        client, cand_b_token, f"/api/v1/orders/{order_id}/payment/proof",
        {"amount": "200.00", "payment_method": "bank_transfer", "reference_number": "REF999"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_confirm_receipt_cross_user_forbidden(
    client, seeded_user, seeded_reviewer, _install_jwt_keys, test_session_factory
):
    """Candidate B cannot confirm receipt on Candidate A's order → 403."""
    from src.persistence.models.auth import User
    from src.security.passwords import hash_password

    async with test_session_factory() as session:
        user_b = User(
            username=f"b-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("correct horse battery staple"),
            role="candidate",
            full_name="B Candidate",
            is_active=True,
            is_locked=False,
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(user_b)
        user_b_data = {"id": user_b.id, "username": user_b.username, "password": "correct horse battery staple"}

    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    await _create_candidate_profile(client, rev_token, user_b_data["id"])

    item_id = await _create_service_item(test_session_factory)
    cand_a_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_a_token, item_id)

    cand_b_token = await login(client, user_b_data)
    resp = await signed_post_json(
        client, cand_b_token,
        f"/api/v1/orders/{order_id}/confirm-receipt",
        None,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_bargaining_offer_cross_user_forbidden(
    client, seeded_user, seeded_reviewer, _install_jwt_keys, test_session_factory
):
    """Candidate B cannot submit a bargaining offer on Candidate A's order → 403."""
    from datetime import datetime, timezone
    from src.persistence.models.auth import User
    from src.security.passwords import hash_password

    async with test_session_factory() as session:
        user_b = User(
            username=f"b-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("correct horse battery staple"),
            role="candidate",
            full_name="B Candidate",
            is_active=True,
            is_locked=False,
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(user_b)
        user_b_data = {"id": user_b.id, "username": user_b.username, "password": "correct horse battery staple"}

    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    await _create_candidate_profile(client, rev_token, user_b_data["id"])

    item_id = await _create_service_item(test_session_factory, bargaining=True)
    cand_a_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_a_token, item_id, pricing_mode="bargaining")

    cand_b_token = await login(client, user_b_data)
    resp = await _submit_offer(client, cand_b_token, order_id, "150.00")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_bargaining_accept_counter_cross_user_forbidden(
    client, seeded_user, seeded_reviewer, _install_jwt_keys, test_session_factory
):
    """Candidate B cannot accept a counter-offer on Candidate A's order → 403."""
    from datetime import datetime, timezone

    from src.persistence.models.auth import User
    from src.security.passwords import hash_password

    async with test_session_factory() as session:
        user_b = User(
            username=f"b-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("correct horse battery staple"),
            role="candidate",
            full_name="B Candidate",
            is_active=True,
            is_locked=False,
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(user_b)
        user_b_data = {"id": user_b.id, "username": user_b.username, "password": "correct horse battery staple"}

    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    await _create_candidate_profile(client, rev_token, user_b_data["id"])

    item_id = await _create_service_item(test_session_factory, bargaining=True)
    cand_a_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_a_token, item_id, pricing_mode="bargaining")

    # Submit offer as candidate A, counter as reviewer
    await _submit_offer(client, cand_a_token, order_id, "150.00")
    await signed_post_json(
        client, rev_token,
        f"/api/v1/orders/{order_id}/bargaining/counter",
        {"counter_amount": "175.00"},
    )

    # Candidate B tries to accept the counter → 403
    cand_b_token = await login(client, user_b_data)
    resp = await signed_post_json(
        client, cand_b_token,
        f"/api/v1/orders/{order_id}/bargaining/accept-counter",
        {
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_bargaining_thread_cross_user_forbidden(
    client, seeded_user, seeded_reviewer, _install_jwt_keys, test_session_factory
):
    """Candidate B cannot read Candidate A's bargaining thread → 403."""
    from datetime import datetime, timezone

    from src.persistence.models.auth import User
    from src.security.passwords import hash_password

    async with test_session_factory() as session:
        user_b = User(
            username=f"b-{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("correct horse battery staple"),
            role="candidate",
            full_name="B Candidate",
            is_active=True,
            is_locked=False,
        )
        session.add(user_b)
        await session.commit()
        await session.refresh(user_b)
        user_b_data = {"id": user_b.id, "username": user_b.username, "password": "correct horse battery staple"}

    rev_token = await login(client, seeded_reviewer)
    await _create_candidate_profile(client, rev_token, seeded_user["id"])
    await _create_candidate_profile(client, rev_token, user_b_data["id"])

    item_id = await _create_service_item(test_session_factory, bargaining=True)
    cand_a_token = await login(client, seeded_user)
    order_id = await _create_order(client, cand_a_token, item_id, pricing_mode="bargaining")

    # Submit an offer to create the bargaining thread
    await _submit_offer(client, cand_a_token, order_id, "140.00")

    # Candidate B tries to read the bargaining thread → 403
    cand_b_token = await login(client, user_b_data)
    resp = await client.get(
        f"/api/v1/orders/{order_id}/bargaining",
        headers={"Authorization": f"Bearer {cand_b_token}"},
    )
    assert resp.status_code == 403
