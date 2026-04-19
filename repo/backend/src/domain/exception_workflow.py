from .enums import ExceptionStatus, ReviewDecision, ReviewStage, UserRole


class WorkflowError(Exception):
    pass


class UnauthorizedReviewError(WorkflowError):
    pass


class InvalidDecisionError(WorkflowError):
    pass


# Ordered review stages: initial (PRCT) → final (REVW)
STAGE_SEQUENCE: list[ReviewStage] = [ReviewStage.initial, ReviewStage.final]

# Which roles may adjudicate each stage
STAGE_ADJUDICATORS: dict[ReviewStage, set[UserRole]] = {
    ReviewStage.initial: {UserRole.proctor, UserRole.reviewer, UserRole.admin},
    ReviewStage.final: {UserRole.reviewer, UserRole.admin},
}

# Which decisions are available at each stage
STAGE_DECISIONS: dict[ReviewStage, set[ReviewDecision]] = {
    ReviewStage.initial: {ReviewDecision.approve, ReviewDecision.reject, ReviewDecision.escalate},
    ReviewStage.final: {ReviewDecision.approve, ReviewDecision.reject},
}

# Status after each (stage, decision) combination
STATUS_AFTER: dict[tuple[ReviewStage, ReviewDecision], ExceptionStatus] = {
    (ReviewStage.initial, ReviewDecision.approve): ExceptionStatus.approved,
    (ReviewStage.initial, ReviewDecision.reject): ExceptionStatus.rejected,
    (ReviewStage.initial, ReviewDecision.escalate): ExceptionStatus.pending_final_review,
    (ReviewStage.final, ReviewDecision.approve): ExceptionStatus.approved,
    (ReviewStage.final, ReviewDecision.reject): ExceptionStatus.rejected,
}


def can_adjudicate(stage: ReviewStage, actor_role: UserRole) -> None:
    """Raise UnauthorizedReviewError if the actor cannot review this stage."""
    allowed = STAGE_ADJUDICATORS.get(stage, set())
    if actor_role not in allowed:
        raise UnauthorizedReviewError(
            f"Role '{actor_role.value}' cannot adjudicate stage '{stage.value}'."
        )


def validate_decision(stage: ReviewStage, decision: ReviewDecision) -> None:
    """Raise InvalidDecisionError if the decision is not available at this stage."""
    allowed = STAGE_DECISIONS.get(stage, set())
    if decision not in allowed:
        raise InvalidDecisionError(
            f"Decision '{decision.value}' is not available at stage '{stage.value}'."
        )


def next_stage(current_stage: ReviewStage) -> ReviewStage | None:
    """Return the next stage in the sequence, or None if current is the final stage."""
    try:
        idx = STAGE_SEQUENCE.index(current_stage)
    except ValueError:
        return None
    next_idx = idx + 1
    if next_idx >= len(STAGE_SEQUENCE):
        return None
    return STAGE_SEQUENCE[next_idx]


def resolve_status(stage: ReviewStage, decision: ReviewDecision) -> ExceptionStatus:
    """Return the exception status that results from this stage/decision combination."""
    key = (stage, decision)
    result = STATUS_AFTER.get(key)
    if result is None:
        raise InvalidDecisionError(
            f"No status resolution defined for stage='{stage.value}' decision='{decision.value}'."
        )
    return result


def initial_stage() -> ReviewStage:
    return STAGE_SEQUENCE[0]


def is_final_stage(stage: ReviewStage) -> bool:
    return stage == STAGE_SEQUENCE[-1]
