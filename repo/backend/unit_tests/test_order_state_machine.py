import pytest
from src.domain.enums import OrderStatus, UserRole
from src.domain.order_state_machine import (
    InvalidTransitionError,
    UnauthorizedTransitionError,
    allowed_next_states,
    is_terminal,
    validate_transition,
)


class TestValidTransitions:
    def test_pending_payment_to_pending_fulfillment_by_reviewer(self):
        validate_transition(
            OrderStatus.pending_payment,
            OrderStatus.pending_fulfillment,
            UserRole.reviewer,
        )

    def test_pending_payment_to_canceled_by_candidate(self):
        validate_transition(
            OrderStatus.pending_payment,
            OrderStatus.canceled,
            UserRole.candidate,
        )

    def test_pending_fulfillment_to_pending_receipt_by_reviewer(self):
        validate_transition(
            OrderStatus.pending_fulfillment,
            OrderStatus.pending_receipt,
            UserRole.reviewer,
        )

    def test_pending_receipt_to_completed_by_candidate(self):
        validate_transition(
            OrderStatus.pending_receipt,
            OrderStatus.completed,
            UserRole.candidate,
        )

    def test_completed_to_refund_in_progress_by_reviewer(self):
        validate_transition(
            OrderStatus.completed,
            OrderStatus.refund_in_progress,
            UserRole.reviewer,
        )

    def test_refund_in_progress_to_refunded_by_admin(self):
        validate_transition(
            OrderStatus.refund_in_progress,
            OrderStatus.refunded,
            UserRole.admin,
        )

    def test_admin_can_cancel_from_pending_payment(self):
        validate_transition(
            OrderStatus.pending_payment,
            OrderStatus.canceled,
            UserRole.admin,
        )


class TestInvalidTransitions:
    def test_completed_to_pending_payment_raises(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(
                OrderStatus.completed,
                OrderStatus.pending_payment,
                UserRole.admin,
            )

    def test_canceled_to_any_raises(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(
                OrderStatus.canceled,
                OrderStatus.pending_payment,
                UserRole.admin,
            )

    def test_refunded_to_any_raises(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(
                OrderStatus.refunded,
                OrderStatus.refund_in_progress,
                UserRole.admin,
            )

    def test_pending_payment_to_completed_raises(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(
                OrderStatus.pending_payment,
                OrderStatus.completed,
                UserRole.admin,
            )


class TestUnauthorizedTransitions:
    def test_candidate_cannot_confirm_payment(self):
        with pytest.raises(UnauthorizedTransitionError):
            validate_transition(
                OrderStatus.pending_payment,
                OrderStatus.pending_fulfillment,
                UserRole.candidate,
            )

    def test_reviewer_cannot_complete_refunded(self):
        with pytest.raises(UnauthorizedTransitionError):
            validate_transition(
                OrderStatus.refund_in_progress,
                OrderStatus.refunded,
                UserRole.reviewer,
            )

    def test_proctor_cannot_confirm_payment(self):
        with pytest.raises(UnauthorizedTransitionError):
            validate_transition(
                OrderStatus.pending_payment,
                OrderStatus.pending_fulfillment,
                UserRole.proctor,
            )


class TestTerminalStates:
    def test_canceled_is_terminal(self):
        assert is_terminal(OrderStatus.canceled) is True

    def test_refunded_is_terminal(self):
        assert is_terminal(OrderStatus.refunded) is True

    def test_completed_is_not_terminal(self):
        assert is_terminal(OrderStatus.completed) is False

    def test_canceled_has_no_next_states(self):
        assert allowed_next_states(OrderStatus.canceled) == set()

    def test_refunded_has_no_next_states(self):
        assert allowed_next_states(OrderStatus.refunded) == set()

    def test_pending_payment_has_two_next_states(self):
        nexts = allowed_next_states(OrderStatus.pending_payment)
        assert OrderStatus.pending_fulfillment in nexts
        assert OrderStatus.canceled in nexts
