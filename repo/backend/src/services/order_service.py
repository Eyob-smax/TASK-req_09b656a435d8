from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..domain.enums import AuditEventType, OrderStatus, UserRole
from ..domain.order_state_machine import InvalidTransitionError, UnauthorizedTransitionError, validate_transition
from ..persistence.models.order import Order, ServiceItem
from ..persistence.repositories.candidate_repo import CandidateRepository
from ..persistence.repositories.order_repo import OrderRepository
from ..schemas.order import (
    OrderCreate,
    OrderEventRead,
    OrderRead,
    ServiceItemRead,
)
from ..security import audit as audit_mod
from ..security.errors import BusinessRuleError, ForbiddenError, ResourceNotFoundError
from ..security.rbac import Actor, UserRole, assert_roles_or_owner


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = OrderRepository(session)

    # ── Service catalog ───────────────────────────────────────────────────────

    async def list_service_items(self) -> list[ServiceItemRead]:
        items = await self._repo.list_service_items()
        result = []
        for item in items:
            available = None
            if item.is_capacity_limited and item.inventory:
                available = item.inventory.total_slots - item.inventory.reserved_count
            result.append(
                ServiceItemRead(
                    id=item.id,
                    item_code=item.item_code,
                    name=item.name,
                    description=item.description,
                    pricing_mode=item.pricing_mode,
                    fixed_price=item.fixed_price,
                    is_capacity_limited=item.is_capacity_limited,
                    bargaining_enabled=item.bargaining_enabled,
                    available_slots=available,
                )
            )
        return result

    # ── Orders ────────────────────────────────────────────────────────────────

    async def create_order(
        self, candidate_actor: Actor, data: OrderCreate
    ) -> OrderRead:
        settings = get_settings()

        # Idempotency is enforced at the route layer by `IdempotencyStore.fetch`
        # (src/api/routes/orders.py) before this service runs, using the full
        # (key, method, path) + body-hash contract from docs/api-spec.md §5.
        # The `idempotency_key` column on `orders` stays populated below so the
        # row records which idempotency token created it, but the service no
        # longer short-circuits on key-match — any caller reaching this point
        # is a verified new-or-fresh request.

        item = await self._repo.get_service_item(data.item_id)
        if item is None or not item.is_active:
            raise ResourceNotFoundError("Service item not found.")

        # Validate pricing mode
        if data.pricing_mode.value == "bargaining" and not item.bargaining_enabled:
            raise BusinessRuleError("Bargaining is not enabled for this service item.")

        # Capacity check and reservation
        if item.is_capacity_limited:
            inventory = await self._repo.lock_inventory(item.id)
            if inventory is None or inventory.reserved_count >= inventory.total_slots:
                raise BusinessRuleError("No capacity available for this service item.")
            await self._repo.reserve_slot(inventory)

        # Resolve the candidate's profile id (FK target for orders.candidate_id)
        c_repo = CandidateRepository(self._session)
        profile = await c_repo.get_by_user_id(uuid.UUID(candidate_actor.user_id))
        if profile is None:
            raise ResourceNotFoundError("Candidate profile not found.")

        auto_cancel_at = _now() + timedelta(minutes=settings.auto_cancel_minutes)
        order = await self._repo.create_order(
            candidate_id=profile.id,
            item_id=item.id,
            pricing_mode=data.pricing_mode.value,
            auto_cancel_at=auto_cancel_at,
            idempotency_key=data.idempotency_key,
        )

        await self._repo.append_event(
            order=order,
            event_type="order_created",
            prev_state=None,
            new_state="pending_payment",
            actor_id=uuid.UUID(candidate_actor.user_id),
            actor_role=candidate_actor.role.value,
        )

        await audit_mod.record_audit(
            self._session,
            event_type=AuditEventType.order_created,
            actor_id=uuid.UUID(candidate_actor.user_id),
            actor_role=candidate_actor.role.value,
            resource_type="order",
            resource_id=str(order.id),
            outcome="created",
            detail={"item_id": str(item.id), "pricing_mode": data.pricing_mode.value},
        )

        # Reload to get full relationships
        order = await self._repo.get_order(order.id)
        return _order_to_read(order)

    async def get_order(self, order_id: uuid.UUID, actor: Actor) -> OrderRead:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        profile = await CandidateRepository(self._session).get_by_id(order.candidate_id)
        owner_user_id = str(profile.user_id) if profile else ""
        assert_roles_or_owner(
            actor,
            [UserRole.reviewer, UserRole.admin, UserRole.proctor],
            owner_user_id,
        )
        return _order_to_read(order)

    async def list_orders(
        self,
        actor: Actor,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[OrderRead], int]:
        if actor.role == UserRole.candidate:
            profile = await CandidateRepository(self._session).get_by_user_id(uuid.UUID(actor.user_id))
            candidate_id = profile.id if profile else None
        else:
            candidate_id = None
        orders, total = await self._repo.list_orders(
            candidate_id=candidate_id,
            status=status,
            page=page,
            page_size=page_size,
        )
        return [_order_to_read(o) for o in orders], total

    async def transition(
        self,
        order_id: uuid.UUID,
        actor: Actor,
        to_state: OrderStatus,
        notes: str | None = None,
    ) -> Order:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")

        from_status = OrderStatus(order.status)
        try:
            validate_transition(from_status, to_state, actor.role)
        except InvalidTransitionError as exc:
            raise BusinessRuleError(str(exc)) from exc
        except UnauthorizedTransitionError as exc:
            raise ForbiddenError(str(exc)) from exc

        extra: dict = {}
        now = _now()
        if to_state == OrderStatus.completed:
            extra["completed_at"] = now
        elif to_state == OrderStatus.canceled:
            extra["canceled_at"] = now
            extra["cancellation_reason"] = notes or "manual_cancel"

        await self._repo.update_order_status(order, to_state.value, **extra)
        await self._repo.append_event(
            order=order,
            event_type="state_transition",
            prev_state=from_status.value,
            new_state=to_state.value,
            actor_id=uuid.UUID(actor.user_id),
            actor_role=actor.role.value,
            notes=notes,
        )
        await audit_mod.record_audit(
            self._session,
            event_type=AuditEventType.order_state_changed,
            actor_id=uuid.UUID(actor.user_id),
            actor_role=actor.role.value,
            resource_type="order",
            resource_id=str(order_id),
            outcome=to_state.value,
            detail={"from": from_status.value, "to": to_state.value},
        )
        return order

    async def cancel(
        self,
        order_id: uuid.UUID,
        actor: Actor,
        reason: str = "",
    ) -> OrderRead:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")

        # Check ownership for candidates
        if actor.role == UserRole.candidate:
            profile = await CandidateRepository(self._session).get_by_id(order.candidate_id)
            owner_user_id = str(profile.user_id) if profile else ""
            assert_roles_or_owner(actor, [], owner_user_id)

        await self.transition(order_id, actor, OrderStatus.canceled, notes=reason)

        # Restore capacity if applicable
        if order.item and order.item.is_capacity_limited:
            inventory = await self._repo.lock_inventory(order.item_id)
            if inventory:
                await self._repo.release_slot(inventory)

        return await self.get_order(order_id, actor)

    async def confirm_receipt(
        self, order_id: uuid.UUID, candidate_actor: Actor
    ) -> OrderRead:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        profile = await CandidateRepository(self._session).get_by_id(order.candidate_id)
        owner_user_id = str(profile.user_id) if profile else ""
        assert_roles_or_owner(candidate_actor, [], owner_user_id)
        await self.transition(
            order_id, candidate_actor, OrderStatus.completed
        )
        return await self.get_order(order_id, candidate_actor)

    async def advance_to_receipt(
        self, order_id: uuid.UUID, reviewer_actor: Actor
    ) -> OrderRead:
        await self.transition(
            order_id, reviewer_actor, OrderStatus.pending_receipt
        )
        return await self.get_order(order_id, reviewer_actor)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _order_to_read(order: Order) -> OrderRead:
    events = []
    if order.events:
        for e in sorted(order.events, key=lambda x: x.sequence_number):
            events.append(
                OrderEventRead(
                    id=e.id,
                    sequence_number=e.sequence_number,
                    event_type=e.event_type,
                    previous_state=OrderStatus(e.previous_state) if e.previous_state else None,
                    new_state=OrderStatus(e.new_state),
                    actor_id=e.actor_id,
                    actor_role=e.actor_role,
                    notes=e.notes,
                    occurred_at=e.occurred_at,
                )
            )
    return OrderRead(
        id=order.id,
        candidate_id=order.candidate_id,
        item_id=order.item_id,
        status=OrderStatus(order.status),
        pricing_mode=order.pricing_mode,
        agreed_price=order.agreed_price,
        auto_cancel_at=order.auto_cancel_at,
        completed_at=order.completed_at,
        canceled_at=order.canceled_at,
        cancellation_reason=order.cancellation_reason,
        created_at=order.created_at,
        updated_at=order.updated_at,
        events=events,
    )
