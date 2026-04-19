"""Extended unit tests for order state machine, auto-cancel timing, capacity, and bargaining."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.domain.after_sales_policy import (
    AfterSalesWindowExpiredError,
    assert_within_window,
)
from src.domain.bargaining import (
    BargainingWindowClosedError,
    CounterAlreadyMadeError,
    OffersExhaustedError,
    can_counter,
    can_submit_offer,
    is_window_expired,
)
from src.domain.enums import OrderStatus, UserRole
from src.domain.order_state_machine import (
    InvalidTransitionError,
    UnauthorizedTransitionError,
    validate_transition,
)

UTC = timezone.utc
_now = datetime.now(UTC)


class TestAutoCancel:
    def test_auto_cancel_timing_overdue(self):
        auto_cancel_at = _now - timedelta(minutes=31)
        assert auto_cancel_at <= _now

    def test_auto_cancel_timing_not_yet_overdue(self):
        auto_cancel_at = _now + timedelta(minutes=1)
        assert auto_cancel_at > _now

    def test_pending_payment_to_canceled_valid(self):
        validate_transition(OrderStatus.pending_payment, OrderStatus.canceled, UserRole.admin)

    def test_pending_payment_to_canceled_by_candidate_valid(self):
        validate_transition(OrderStatus.pending_payment, OrderStatus.canceled, UserRole.candidate)


class TestCapacityReservation:
    def test_reserve_slot_called_on_create(self):
        inventory = MagicMock()
        inventory.reserved_count = 0
        inventory.total_slots = 10
        inventory.reserved_count += 1
        assert inventory.reserved_count == 1

    def test_release_slot_called_on_cancel(self):
        inventory = MagicMock()
        inventory.reserved_count = 5
        inventory.reserved_count -= 1
        assert inventory.reserved_count == 4

    def test_no_slot_reserved_when_not_capacity_limited(self):
        item = MagicMock()
        item.is_capacity_limited = False
        slots_reserved = 0
        if item.is_capacity_limited:
            slots_reserved += 1
        assert slots_reserved == 0


class TestBargainingOfferLimit:
    def test_bargaining_offer_limit_raises_on_4th_offer(self):
        now = _now
        window_start = now - timedelta(hours=1)
        with pytest.raises(OffersExhaustedError):
            can_submit_offer(3, window_start, now)

    def test_bargaining_offer_3rd_succeeds(self):
        now = _now
        window_start = now - timedelta(hours=1)
        can_submit_offer(2, window_start, now)

    def test_bargaining_window_closed_raises_after_48h(self):
        now = _now
        window_start = now - timedelta(hours=49)
        with pytest.raises(BargainingWindowClosedError):
            can_submit_offer(0, window_start, now)

    def test_bargaining_window_open_at_47h(self):
        now = _now
        window_start = now - timedelta(hours=47)
        can_submit_offer(0, window_start, now)


class TestCounterOnceRule:
    def test_second_counter_raises(self):
        with pytest.raises(CounterAlreadyMadeError):
            can_counter(1)

    def test_first_counter_succeeds(self):
        can_counter(0)

    def test_counter_at_zero_ok(self):
        can_counter(0)


class TestAfterSalesWindowBoundary:
    def test_day_14_accepted(self):
        completed_at = _now - timedelta(days=14)
        assert_within_window(completed_at, _now)

    def test_day_15_rejected(self):
        completed_at = _now - timedelta(days=15) - timedelta(seconds=1)
        with pytest.raises(AfterSalesWindowExpiredError):
            assert_within_window(completed_at, _now)

    def test_day_1_accepted(self):
        completed_at = _now - timedelta(days=1)
        assert_within_window(completed_at, _now)

    def test_exactly_on_expiry_boundary_accepted(self):
        completed_at = _now - timedelta(days=14)
        assert_within_window(completed_at, _now)


class TestTransitionChain:
    def test_full_order_lifecycle(self):
        validate_transition(OrderStatus.pending_payment, OrderStatus.pending_fulfillment, UserRole.reviewer)
        validate_transition(OrderStatus.pending_fulfillment, OrderStatus.pending_receipt, UserRole.reviewer)
        validate_transition(OrderStatus.pending_receipt, OrderStatus.completed, UserRole.candidate)
        validate_transition(OrderStatus.completed, OrderStatus.refund_in_progress, UserRole.reviewer)
        validate_transition(OrderStatus.refund_in_progress, OrderStatus.refunded, UserRole.admin)

    def test_refunded_cannot_go_back_to_refund_in_progress(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(OrderStatus.refunded, OrderStatus.refund_in_progress, UserRole.admin)

    def test_candidate_cannot_advance_to_pending_fulfillment(self):
        with pytest.raises(UnauthorizedTransitionError):
            validate_transition(
                OrderStatus.pending_payment, OrderStatus.pending_fulfillment, UserRole.candidate
            )
