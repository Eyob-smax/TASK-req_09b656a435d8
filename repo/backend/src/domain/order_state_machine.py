from .enums import OrderStatus, UserRole


class InvalidTransitionError(Exception):
    def __init__(self, from_state: OrderStatus, to_state: OrderStatus, reason: str = ""):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Transition {from_state.value} → {to_state.value} is not permitted. {reason}".strip()
        )


class UnauthorizedTransitionError(Exception):
    def __init__(self, role: UserRole, from_state: OrderStatus, to_state: OrderStatus):
        super().__init__(
            f"Role '{role.value}' may not perform {from_state.value} → {to_state.value}"
        )


# Valid state transitions: from_state → {allowed to_states}
VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.pending_payment: {
        OrderStatus.pending_fulfillment,
        OrderStatus.canceled,
    },
    OrderStatus.pending_fulfillment: {
        OrderStatus.pending_receipt,
        OrderStatus.canceled,
    },
    OrderStatus.pending_receipt: {
        OrderStatus.completed,
        OrderStatus.canceled,
    },
    OrderStatus.completed: {
        OrderStatus.refund_in_progress,
    },
    OrderStatus.canceled: set(),
    OrderStatus.refund_in_progress: {
        OrderStatus.refunded,
    },
    OrderStatus.refunded: set(),
}

# Who may perform each transition: (from, to) → {allowed roles}
TRANSITION_PERMISSIONS: dict[tuple[OrderStatus, OrderStatus], set[UserRole]] = {
    (OrderStatus.pending_payment, OrderStatus.pending_fulfillment): {
        UserRole.reviewer, UserRole.admin
    },
    (OrderStatus.pending_payment, OrderStatus.canceled): {
        UserRole.candidate, UserRole.reviewer, UserRole.admin
    },
    (OrderStatus.pending_fulfillment, OrderStatus.pending_receipt): {
        UserRole.reviewer, UserRole.admin
    },
    (OrderStatus.pending_fulfillment, OrderStatus.canceled): {
        UserRole.reviewer, UserRole.admin
    },
    (OrderStatus.pending_receipt, OrderStatus.completed): {
        UserRole.candidate, UserRole.reviewer, UserRole.admin
    },
    (OrderStatus.pending_receipt, OrderStatus.canceled): {
        UserRole.reviewer, UserRole.admin
    },
    (OrderStatus.completed, OrderStatus.refund_in_progress): {
        UserRole.reviewer, UserRole.admin
    },
    (OrderStatus.refund_in_progress, OrderStatus.refunded): {
        UserRole.admin
    },
}

TERMINAL_STATES: frozenset[OrderStatus] = frozenset(
    {OrderStatus.canceled, OrderStatus.refunded}
)


def validate_transition(
    from_state: OrderStatus,
    to_state: OrderStatus,
    actor_role: UserRole,
) -> None:
    """Raise if the transition is structurally invalid or the actor lacks permission."""
    allowed_targets = VALID_TRANSITIONS.get(from_state, set())
    if to_state not in allowed_targets:
        raise InvalidTransitionError(from_state, to_state)

    allowed_roles = TRANSITION_PERMISSIONS.get((from_state, to_state), set())
    if actor_role not in allowed_roles:
        raise UnauthorizedTransitionError(actor_role, from_state, to_state)


def is_terminal(state: OrderStatus) -> bool:
    return state in TERMINAL_STATES


def allowed_next_states(from_state: OrderStatus) -> set[OrderStatus]:
    return VALID_TRANSITIONS.get(from_state, set()).copy()
