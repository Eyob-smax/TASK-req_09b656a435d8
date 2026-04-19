import uuid

import pytest
from pydantic import ValidationError

from src.schemas.auth import LoginRequest, PasswordChangeRequest
from src.schemas.bargaining import OfferCreate
from src.schemas.common import ErrorBody, ErrorResponse, SuccessResponse, make_error, make_success
from src.schemas.document import DocumentReviewCreate
from src.schemas.order import OrderCreate, RefundCreate
from src.domain.enums import DocumentStatus, PricingMode


class TestLoginRequest:
    def test_valid_login(self):
        req = LoginRequest(
            username="user1",
            password="SecurePass123!",
            nonce="abc123",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert req.username == "user1"

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(
                username="user1",
                password="short",
                nonce="abc123",
                timestamp="2025-01-01T00:00:00Z",
            )
        errors = exc_info.value.errors()
        assert any("password" in str(e["loc"]) for e in errors)

    def test_empty_username_raises(self):
        with pytest.raises(ValidationError):
            LoginRequest(
                username="",
                password="SecurePass123!",
                nonce="abc123",
                timestamp="2025-01-01T00:00:00Z",
            )


class TestPasswordChangeRequest:
    def test_new_password_min_12_chars_accepted(self):
        req = PasswordChangeRequest(
            current_password="old",
            new_password="SecureNew12345!",
            nonce="abc",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert req.new_password == "SecureNew12345!"

    def test_new_password_11_chars_rejected(self):
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password="old",
                new_password="ShortPass1!",
                nonce="abc",
                timestamp="2025-01-01T00:00:00Z",
            )


class TestOfferCreate:
    def test_positive_amount_accepted(self):
        offer = OfferCreate(amount="100.00", nonce="n1", timestamp="2025-01-01T00:00:00Z")
        assert offer.amount > 0

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError):
            OfferCreate(amount="0", nonce="n1", timestamp="2025-01-01T00:00:00Z")

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            OfferCreate(amount="-50.00", nonce="n1", timestamp="2025-01-01T00:00:00Z")


class TestDocumentReviewCreate:
    def test_approved_without_reason_passes(self):
        r = DocumentReviewCreate(
            version_id=uuid.uuid4(),
            status=DocumentStatus.approved,
        )
        assert r.status == DocumentStatus.approved

    def test_needs_resubmission_with_reason_passes(self):
        r = DocumentReviewCreate(
            version_id=uuid.uuid4(),
            status=DocumentStatus.needs_resubmission,
            resubmission_reason="ID document is expired.",
        )
        assert r.resubmission_reason is not None

    def test_needs_resubmission_without_reason_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            DocumentReviewCreate(
                version_id=uuid.uuid4(),
                status=DocumentStatus.needs_resubmission,
            )
        assert "resubmission_reason" in str(exc_info.value)

    def test_rejected_without_reason_passes(self):
        DocumentReviewCreate(
            version_id=uuid.uuid4(),
            status=DocumentStatus.rejected,
        )


class TestOrderCreate:
    def test_valid_order_create(self):
        o = OrderCreate(item_id=uuid.uuid4(), pricing_mode=PricingMode.fixed)
        assert o.item_id is not None

    def test_missing_item_id_raises(self):
        with pytest.raises(ValidationError):
            OrderCreate(pricing_mode=PricingMode.fixed)


class TestErrorEnvelopeShape:
    def test_make_error_returns_correct_shape(self):
        resp = make_error("SOME_CODE", "Something went wrong")
        assert resp.success is False
        assert resp.error.code == "SOME_CODE"
        assert resp.error.message == "Something went wrong"
        assert isinstance(resp.meta.trace_id, str)

    def test_make_success_returns_correct_shape(self):
        resp = make_success({"key": "value"})
        assert resp.success is True
        assert resp.data == {"key": "value"}
        assert isinstance(resp.meta.trace_id, str)

    def test_error_response_serializes_to_dict(self):
        resp = make_error("ERR", "msg")
        d = resp.model_dump()
        assert d["success"] is False
        assert d["error"]["code"] == "ERR"
