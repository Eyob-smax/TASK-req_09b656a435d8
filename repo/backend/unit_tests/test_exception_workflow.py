import pytest

from src.domain.enums import ExceptionStatus, ReviewDecision, ReviewStage, UserRole
from src.domain.exception_workflow import (
    InvalidDecisionError,
    UnauthorizedReviewError,
    can_adjudicate,
    initial_stage,
    is_final_stage,
    next_stage,
    resolve_status,
    validate_decision,
)


class TestStageSequence:
    def test_initial_stage_is_initial(self):
        assert initial_stage() == ReviewStage.initial

    def test_next_stage_after_initial_is_final(self):
        assert next_stage(ReviewStage.initial) == ReviewStage.final

    def test_next_stage_after_final_is_none(self):
        assert next_stage(ReviewStage.final) is None

    def test_initial_is_not_final_stage(self):
        assert is_final_stage(ReviewStage.initial) is False

    def test_final_is_final_stage(self):
        assert is_final_stage(ReviewStage.final) is True


class TestCanAdjudicate:
    def test_proctor_can_adjudicate_initial(self):
        can_adjudicate(ReviewStage.initial, UserRole.proctor)

    def test_reviewer_can_adjudicate_initial(self):
        can_adjudicate(ReviewStage.initial, UserRole.reviewer)

    def test_reviewer_can_adjudicate_final(self):
        can_adjudicate(ReviewStage.final, UserRole.reviewer)

    def test_admin_can_adjudicate_both(self):
        can_adjudicate(ReviewStage.initial, UserRole.admin)
        can_adjudicate(ReviewStage.final, UserRole.admin)

    def test_proctor_cannot_adjudicate_final(self):
        with pytest.raises(UnauthorizedReviewError):
            can_adjudicate(ReviewStage.final, UserRole.proctor)

    def test_candidate_cannot_adjudicate_initial(self):
        with pytest.raises(UnauthorizedReviewError):
            can_adjudicate(ReviewStage.initial, UserRole.candidate)

    def test_candidate_cannot_adjudicate_final(self):
        with pytest.raises(UnauthorizedReviewError):
            can_adjudicate(ReviewStage.final, UserRole.candidate)


class TestValidateDecision:
    def test_escalate_allowed_at_initial_stage(self):
        validate_decision(ReviewStage.initial, ReviewDecision.escalate)

    def test_escalate_not_allowed_at_final_stage(self):
        with pytest.raises(InvalidDecisionError):
            validate_decision(ReviewStage.final, ReviewDecision.escalate)

    def test_approve_allowed_at_both_stages(self):
        validate_decision(ReviewStage.initial, ReviewDecision.approve)
        validate_decision(ReviewStage.final, ReviewDecision.approve)

    def test_reject_allowed_at_both_stages(self):
        validate_decision(ReviewStage.initial, ReviewDecision.reject)
        validate_decision(ReviewStage.final, ReviewDecision.reject)


class TestResolveStatus:
    def test_initial_approve_gives_approved(self):
        assert resolve_status(ReviewStage.initial, ReviewDecision.approve) == ExceptionStatus.approved

    def test_initial_reject_gives_rejected(self):
        assert resolve_status(ReviewStage.initial, ReviewDecision.reject) == ExceptionStatus.rejected

    def test_initial_escalate_gives_pending_final_review(self):
        assert resolve_status(ReviewStage.initial, ReviewDecision.escalate) == ExceptionStatus.pending_final_review

    def test_final_approve_gives_approved(self):
        assert resolve_status(ReviewStage.final, ReviewDecision.approve) == ExceptionStatus.approved

    def test_final_reject_gives_rejected(self):
        assert resolve_status(ReviewStage.final, ReviewDecision.reject) == ExceptionStatus.rejected
