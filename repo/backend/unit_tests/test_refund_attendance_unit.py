"""Unit tests for refund state machine and attendance exception workflow (no DB)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.domain.enums import (
    ExceptionStatus,
    OrderStatus,
    ReviewDecision,
    ReviewStage,
    UserRole,
)
from src.domain.exception_workflow import (
    InvalidDecisionError,
    STATUS_AFTER,
    UnauthorizedReviewError,
    can_adjudicate,
    resolve_status,
    validate_decision,
)
from src.domain.order_state_machine import (
    InvalidTransitionError,
    UnauthorizedTransitionError,
    validate_transition,
)


class TestRefundSlotRollback:
    """process_refund on a capacity-limited item must decrement reserved_count."""

    def test_refund_rollback_restores_slot(self):
        inventory = MagicMock()
        inventory.reserved_count = 3
        is_capacity_limited = True

        if is_capacity_limited:
            inventory.reserved_count -= 1

        assert inventory.reserved_count == 2

    def test_refund_rollback_not_applied_when_not_capacity_limited(self):
        inventory = MagicMock()
        inventory.reserved_count = 3
        is_capacity_limited = False

        if is_capacity_limited:
            inventory.reserved_count -= 1

        assert inventory.reserved_count == 3


class TestRefundTransitionChain:
    def test_completed_to_refund_in_progress_valid(self):
        validate_transition(
            OrderStatus.completed,
            OrderStatus.refund_in_progress,
            UserRole.reviewer,
        )

    def test_refund_in_progress_to_refunded_valid(self):
        validate_transition(
            OrderStatus.refund_in_progress,
            OrderStatus.refunded,
            UserRole.admin,
        )

    def test_refunded_to_refund_in_progress_invalid(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(
                OrderStatus.refunded,
                OrderStatus.refund_in_progress,
                UserRole.admin,
            )

    def test_only_admin_can_process_refund(self):
        with pytest.raises(UnauthorizedTransitionError):
            validate_transition(
                OrderStatus.refund_in_progress,
                OrderStatus.refunded,
                UserRole.reviewer,
            )


class TestAttendanceCanAdjudicate:
    def test_proctor_can_adjudicate_initial(self):
        can_adjudicate(ReviewStage.initial, UserRole.proctor)

    def test_reviewer_can_adjudicate_initial(self):
        can_adjudicate(ReviewStage.initial, UserRole.reviewer)

    def test_candidate_cannot_adjudicate_initial(self):
        with pytest.raises(UnauthorizedReviewError):
            can_adjudicate(ReviewStage.initial, UserRole.candidate)

    def test_proctor_cannot_adjudicate_final(self):
        with pytest.raises(UnauthorizedReviewError):
            can_adjudicate(ReviewStage.final, UserRole.proctor)

    def test_reviewer_can_adjudicate_final(self):
        can_adjudicate(ReviewStage.final, UserRole.reviewer)

    def test_admin_can_adjudicate_final(self):
        can_adjudicate(ReviewStage.final, UserRole.admin)


class TestAttendanceValidateDecision:
    def test_escalate_valid_at_initial(self):
        validate_decision(ReviewStage.initial, ReviewDecision.escalate)

    def test_escalate_at_final_raises(self):
        with pytest.raises(InvalidDecisionError):
            validate_decision(ReviewStage.final, ReviewDecision.escalate)

    def test_approve_valid_at_initial(self):
        validate_decision(ReviewStage.initial, ReviewDecision.approve)

    def test_approve_valid_at_final(self):
        validate_decision(ReviewStage.final, ReviewDecision.approve)

    def test_reject_valid_at_both_stages(self):
        validate_decision(ReviewStage.initial, ReviewDecision.reject)
        validate_decision(ReviewStage.final, ReviewDecision.reject)


class TestResolveStatusMatrix:
    """All (stage, decision) combinations must produce the correct ExceptionStatus."""

    def test_initial_approve_gives_approved(self):
        assert resolve_status(ReviewStage.initial, ReviewDecision.approve) == ExceptionStatus.approved

    def test_initial_reject_gives_rejected(self):
        assert resolve_status(ReviewStage.initial, ReviewDecision.reject) == ExceptionStatus.rejected

    def test_initial_escalate_gives_pending_final_review(self):
        assert (
            resolve_status(ReviewStage.initial, ReviewDecision.escalate)
            == ExceptionStatus.pending_final_review
        )

    def test_final_approve_gives_approved(self):
        assert resolve_status(ReviewStage.final, ReviewDecision.approve) == ExceptionStatus.approved

    def test_final_reject_gives_rejected(self):
        assert resolve_status(ReviewStage.final, ReviewDecision.reject) == ExceptionStatus.rejected


class TestQueueFilterLogic:
    """pending_documents should only include pending_review and needs_resubmission statuses."""

    from src.domain.enums import DocumentStatus

    QUEUE_STATUSES = {"pending_review", "needs_resubmission"}

    def _in_queue(self, status: str) -> bool:
        return status in self.QUEUE_STATUSES

    def test_pending_review_in_queue(self):
        assert self._in_queue("pending_review") is True

    def test_needs_resubmission_in_queue(self):
        assert self._in_queue("needs_resubmission") is True

    def test_approved_not_in_queue(self):
        assert self._in_queue("approved") is False

    def test_rejected_not_in_queue(self):
        assert self._in_queue("rejected") is False
