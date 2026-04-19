"""BE-API: Rejection coverage for routes signed under audit-5 B2 + audit-1 remediation.

Every mutation endpoint declared with `require_signed_request` must reject
unsigned requests with 400 SIGNATURE_INVALID. This file asserts that contract for
all 16 signed mutation routes; positive-path coverage (signed request succeeds)
lives in the retrofitted integration tests (test_payment.py,
test_refund_after_sales.py, test_attendance.py, test_orders.py) where each
signed_post_json / signed_post_multipart call is an end-to-end success proof.

Covered rejection contracts (audit-5 B2):
  POST /api/v1/orders/{order_id}/payment/proof
  POST /api/v1/orders/{order_id}/payment/confirm
  POST /api/v1/orders/{order_id}/voucher
  POST /api/v1/orders/{order_id}/milestones
  POST /api/v1/orders/{order_id}/refund
  POST /api/v1/orders/{order_id}/refund/process
  POST /api/v1/orders/{order_id}/after-sales
  POST /api/v1/orders/{order_id}/after-sales/{request_id}/resolve
  POST /api/v1/attendance/exceptions/{exception_id}/proof
  POST /api/v1/attendance/exceptions/{exception_id}/review

Additional coverage (audit-1 remediation — close the state-transition gap so every
order-state POST is device-bound + anti-replay):
  POST /api/v1/orders/{order_id}/cancel
  POST /api/v1/orders/{order_id}/confirm-receipt
  POST /api/v1/orders/{order_id}/advance
  POST /api/v1/orders/{order_id}/bargaining/accept
  POST /api/v1/orders/{order_id}/bargaining/counter
  POST /api/v1/orders/{order_id}/bargaining/accept-counter
"""
from __future__ import annotations

import io
import uuid

import pytest

from .conftest import login


def _assert_signature_rejected(resp) -> None:
    """Common assertion: 400 with SIGNATURE_INVALID code and no mutation applied."""
    assert resp.status_code == 400, f"expected 400, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SIGNATURE_INVALID", body


# ─────────────────────────────────────────────────────────────────────────────
# /orders/{id}/payment/*  —  signing enforced for financial mutations.
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_payment_proof_unsigned_rejected(client, seeded_user):
    """POST /payment/proof without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_user)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/payment/proof",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": "100.00", "payment_method": "bank_transfer"},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_payment_confirm_unsigned_rejected(client, seeded_reviewer):
    """POST /payment/confirm without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_reviewer)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/payment/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": "100.00", "payment_method": "bank_transfer"},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_voucher_issue_unsigned_rejected(client, seeded_reviewer):
    """POST /voucher without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_reviewer)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/voucher",
        headers={"Authorization": f"Bearer {token}"},
        json={"notes": "issue"},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_milestones_create_unsigned_rejected(client, seeded_reviewer):
    """POST /milestones without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_reviewer)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/milestones",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Kickoff", "description": "Start"},
    )
    _assert_signature_rejected(resp)


# ─────────────────────────────────────────────────────────────────────────────
# /orders/{id}/refund/*  —  signing enforced for refund mutations.
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refund_initiate_unsigned_rejected(client, seeded_reviewer):
    """POST /refund without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_reviewer)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/refund",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": "100.00", "reason": "test"},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_refund_process_unsigned_rejected(client, seeded_admin):
    """POST /refund/process without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_admin)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/refund/process",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    _assert_signature_rejected(resp)


# ─────────────────────────────────────────────────────────────────────────────
# /orders/{id}/after-sales/*  —  signing enforced for workflow mutations.
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_after_sales_submit_unsigned_rejected(client, seeded_user):
    """POST /after-sales without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_user)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/after-sales",
        headers={"Authorization": f"Bearer {token}"},
        json={"request_type": "complaint", "description": "test"},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_after_sales_resolve_unsigned_rejected(client, seeded_reviewer):
    """POST /after-sales/{req}/resolve without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_reviewer)
    fake_order_id = uuid.uuid4()
    fake_request_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/after-sales/{fake_request_id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
        params={"resolution_notes": "test"},
    )
    _assert_signature_rejected(resp)


# ─────────────────────────────────────────────────────────────────────────────
# /attendance/exceptions/{id}/*  —  signing enforced for workflow mutations.
# ─────────────────────────────────────────────────────────────────────────────


_MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF"


@pytest.mark.asyncio
async def test_exception_proof_unsigned_rejected(client, seeded_user):
    """POST /exceptions/{id}/proof without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_user)
    fake_exception_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/attendance/exceptions/{fake_exception_id}/proof",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("proof.pdf", io.BytesIO(_MINIMAL_PDF), "application/pdf")},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_exception_review_unsigned_rejected(client, seeded_reviewer):
    """POST /exceptions/{id}/review without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_reviewer)
    fake_exception_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/attendance/exceptions/{fake_exception_id}/review",
        headers={"Authorization": f"Bearer {token}"},
        json={"decision": "approve"},
    )
    _assert_signature_rejected(resp)


# ─────────────────────────────────────────────────────────────────────────────
# /orders/{id}/{cancel,confirm-receipt,advance}  —  audit-1 remediation.
# State transitions must be device-bound + anti-replay.
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_order_cancel_unsigned_rejected(client, seeded_user):
    """POST /orders/{id}/cancel without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_user)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"notes": "test"},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_order_confirm_receipt_unsigned_rejected(client, seeded_user):
    """POST /orders/{id}/confirm-receipt without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_user)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/confirm-receipt",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_order_advance_unsigned_rejected(client, seeded_reviewer):
    """POST /orders/{id}/advance without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_reviewer)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/advance",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    _assert_signature_rejected(resp)


# ─────────────────────────────────────────────────────────────────────────────
# /orders/{id}/bargaining/{accept,counter,accept-counter}  —  audit-1 remediation.
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bargaining_accept_unsigned_rejected(client, seeded_reviewer):
    """POST /bargaining/accept without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_reviewer)
    fake_order_id = uuid.uuid4()
    fake_offer_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/bargaining/accept",
        headers={"Authorization": f"Bearer {token}"},
        json={"offer_id": str(fake_offer_id)},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_bargaining_counter_unsigned_rejected(client, seeded_reviewer):
    """POST /bargaining/counter without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_reviewer)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/bargaining/counter",
        headers={"Authorization": f"Bearer {token}"},
        json={"counter_amount": "90.00"},
    )
    _assert_signature_rejected(resp)


@pytest.mark.asyncio
async def test_bargaining_accept_counter_unsigned_rejected(client, seeded_user):
    """POST /bargaining/accept-counter without signing headers → 400 SIGNATURE_INVALID."""
    token = await login(client, seeded_user)
    fake_order_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/orders/{fake_order_id}/bargaining/accept-counter",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    _assert_signature_rejected(resp)
