from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.enums import AuditEventType, OrderStatus, UserRole
from ..persistence.repositories.candidate_repo import CandidateRepository
from ..persistence.repositories.order_repo import OrderRepository
from ..schemas.order import RefundCreate, RefundRead
from ..security import audit as audit_mod
from ..security.errors import BusinessRuleError, ResourceNotFoundError
from ..security.rbac import Actor, assert_roles_or_owner
from .order_service import OrderService


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class RefundService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = OrderRepository(session)
        self._order_svc = OrderService(session)

    async def initiate_refund(
        self,
        order_id: uuid.UUID,
        reviewer_actor: Actor,
        data: RefundCreate,
    ) -> RefundRead:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")

        existing = await self._repo.get_refund_record(order_id)
        if existing is not None:
            raise BusinessRuleError("A refund record already exists for this order.")

        await self._order_svc.transition(
            order_id, reviewer_actor, OrderStatus.refund_in_progress,
            notes="refund_initiated"
        )
        record = await self._repo.create_refund_record(
            order_id=order_id,
            amount=data.amount,
            initiated_by=uuid.UUID(reviewer_actor.user_id),
            reason=data.reason,
        )
        return _refund_to_read(record)

    async def process_refund(
        self, order_id: uuid.UUID, admin_actor: Actor
    ) -> RefundRead:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")

        record = await self._repo.get_refund_record(order_id)
        if record is None:
            raise ResourceNotFoundError("Refund record not found.")
        if record.processed_by is not None:
            raise BusinessRuleError("Refund has already been processed.")

        await self._order_svc.transition(
            order_id, admin_actor, OrderStatus.refunded, notes="refund_processed"
        )
        await self._repo.process_refund(record, uuid.UUID(admin_actor.user_id))

        # Restore capacity slot if applicable
        if order.item and order.item.is_capacity_limited:
            now = _now()
            inventory = await self._repo.lock_inventory(order.item_id)
            if inventory:
                await self._repo.release_slot(inventory)
                await self._repo.create_rollback_event(
                    refund_id=record.id,
                    order_id=order.id,
                    item_id=order.item_id,
                    slots_restored=1,
                    rollback_reason="refund_processed",
                    rolled_back_at=now,
                )
                record.rollback_applied = True
                await self._session.flush()

        await audit_mod.record_audit(
            self._session,
            event_type=AuditEventType.order_state_changed,
            actor_id=uuid.UUID(admin_actor.user_id),
            actor_role=admin_actor.role.value,
            resource_type="refund",
            resource_id=str(record.id),
            outcome="refunded",
            detail={"rollback_applied": record.rollback_applied},
        )
        return _refund_to_read(record)

    async def get_refund(self, order_id: uuid.UUID, actor: Actor) -> RefundRead | None:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        profile = await CandidateRepository(self._session).get_by_id(order.candidate_id)
        owner_user_id = str(profile.user_id) if profile else ""
        assert_roles_or_owner(actor, [UserRole.reviewer, UserRole.admin], owner_user_id)
        record = await self._repo.get_refund_record(order_id)
        if record is None:
            return None
        return _refund_to_read(record)


def _refund_to_read(record) -> RefundRead:
    return RefundRead(
        id=record.id,
        order_id=record.order_id,
        amount=record.amount,
        initiated_by=record.initiated_by,
        initiated_at=record.initiated_at,
        processed_by=record.processed_by,
        processed_at=record.processed_at,
        reason=record.reason,
        rollback_applied=record.rollback_applied,
    )
