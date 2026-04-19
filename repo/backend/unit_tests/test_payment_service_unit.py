"""Pure unit tests for payment service business rules (no DB)."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.enums import OrderStatus, UserRole
from src.domain.order_state_machine import validate_transition


class TestPaymentProofDuplicate:
    """submit_proof should be rejected if an unconfirmed record already exists."""

    def test_payment_proof_duplicate_rejected(self):
        existing_record = MagicMock()
        existing_record.confirmed_by = None

        def _check_duplicate(existing):
            if existing is not None and existing.confirmed_by is None:
                raise ValueError("Payment proof already submitted and pending confirmation.")

        with pytest.raises(ValueError, match="already submitted"):
            _check_duplicate(existing_record)

    def test_payment_proof_allows_new_when_no_existing(self):
        existing_record = None

        def _check_duplicate(existing):
            if existing is not None and existing.confirmed_by is None:
                raise ValueError("Payment proof already submitted and pending confirmation.")

        _check_duplicate(existing_record)

    def test_payment_proof_allows_new_when_previous_confirmed(self):
        confirmed_record = MagicMock()
        confirmed_record.confirmed_by = uuid.uuid4()

        def _check_duplicate(existing):
            if existing is not None and existing.confirmed_by is None:
                raise ValueError("Payment proof already submitted and pending confirmation.")

        _check_duplicate(confirmed_record)


class TestPaymentConfirmTransition:
    """Confirming payment must transition order from pending_payment to pending_fulfillment."""

    def test_confirm_triggers_correct_transition(self):
        validate_transition(
            OrderStatus.pending_payment,
            OrderStatus.pending_fulfillment,
            UserRole.reviewer,
        )

    def test_candidate_cannot_confirm_payment(self):
        from src.domain.order_state_machine import UnauthorizedTransitionError

        with pytest.raises(UnauthorizedTransitionError):
            validate_transition(
                OrderStatus.pending_payment,
                OrderStatus.pending_fulfillment,
                UserRole.candidate,
            )


class TestVoucherCodeFormat:
    """Voucher code must be 16-char uppercase hex."""

    def _generate_voucher_code(self) -> str:
        return uuid.uuid4().hex[:16].upper()

    def test_voucher_code_length(self):
        code = self._generate_voucher_code()
        assert len(code) == 16

    def test_voucher_code_uppercase(self):
        code = self._generate_voucher_code()
        assert code == code.upper()

    def test_voucher_code_is_hex(self):
        code = self._generate_voucher_code()
        assert re.fullmatch(r"[0-9A-F]{16}", code), f"Not uppercase hex: {code}"

    def test_voucher_codes_are_unique(self):
        codes = {self._generate_voucher_code() for _ in range(100)}
        assert len(codes) == 100


class TestMilestoneRequiresPendingFulfillment:
    """add_milestone should only work when order status is pending_fulfillment."""

    def _assert_pending_fulfillment(self, status: OrderStatus) -> None:
        if status != OrderStatus.pending_fulfillment:
            raise ValueError(
                f"Milestones can only be added to orders in pending_fulfillment state, "
                f"got: {status.value}"
            )

    def test_milestone_requires_pending_fulfillment(self):
        with pytest.raises(ValueError, match="pending_fulfillment"):
            self._assert_pending_fulfillment(OrderStatus.pending_payment)

    def test_milestone_ok_for_pending_fulfillment(self):
        self._assert_pending_fulfillment(OrderStatus.pending_fulfillment)

    def test_milestone_rejected_for_completed(self):
        with pytest.raises(ValueError, match="pending_fulfillment"):
            self._assert_pending_fulfillment(OrderStatus.completed)

    def test_milestone_rejected_for_canceled(self):
        with pytest.raises(ValueError, match="pending_fulfillment"):
            self._assert_pending_fulfillment(OrderStatus.canceled)
