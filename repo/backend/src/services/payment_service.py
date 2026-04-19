from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.enums import AuditEventType, OrderStatus, UserRole
from ..persistence.models.order import FulfillmentMilestone, PaymentRecord, Voucher
from ..persistence.repositories.candidate_repo import CandidateRepository
from ..persistence.repositories.order_repo import OrderRepository
from ..schemas.order import (
    MilestoneCreate,
    MilestoneRead,
    PaymentConfirmRequest,
    PaymentProofSubmit,
    VoucherCreate,
    VoucherRead,
)
from ..security import audit as audit_mod
from ..security.errors import BusinessRuleError, ForbiddenError, ResourceNotFoundError
from ..security.rbac import Actor, assert_roles_or_owner
from .order_service import OrderService


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = OrderRepository(session)
        self._order_svc = OrderService(session)

    async def submit_proof(
        self,
        order_id: uuid.UUID,
        candidate_actor: Actor,
        data: PaymentProofSubmit,
    ) -> PaymentRecord:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        profile = await CandidateRepository(self._session).get_by_id(order.candidate_id)
        owner_user_id = str(profile.user_id) if profile else ""
        assert_roles_or_owner(candidate_actor, [], owner_user_id)
        if order.status != OrderStatus.pending_payment.value:
            raise BusinessRuleError("Payment proof can only be submitted for pending_payment orders.")

        existing = await self._repo.get_payment_record(order_id)
        if existing is not None:
            raise BusinessRuleError("A payment submission already exists for this order.")

        record = await self._repo.create_payment_record(
            order_id=order_id,
            amount=data.amount,
            payment_method=data.payment_method,
            reference_number=data.reference_number,
            notes=data.notes,
        )
        return record

    async def confirm_payment(
        self,
        order_id: uuid.UUID,
        reviewer_actor: Actor,
        data: PaymentConfirmRequest,
    ):
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")

        record = await self._repo.get_payment_record(order_id)
        if record is None:
            raise BusinessRuleError("No payment submission found for this order.")
        if record.confirmed_by is not None:
            raise BusinessRuleError("Payment has already been confirmed.")

        await self._repo.confirm_payment(record, uuid.UUID(reviewer_actor.user_id))
        await self._order_svc.transition(
            order_id, reviewer_actor, OrderStatus.pending_fulfillment,
            notes="payment_confirmed"
        )

        from ..schemas.order import OrderRead
        return await self._order_svc.get_order(order_id, reviewer_actor)

    async def issue_voucher(
        self,
        order_id: uuid.UUID,
        reviewer_actor: Actor,
        data: VoucherCreate,
    ) -> VoucherRead:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        if order.status != OrderStatus.pending_fulfillment.value:
            raise BusinessRuleError("Vouchers can only be issued for pending_fulfillment orders.")

        existing = await self._repo.get_voucher(order_id)
        if existing is not None:
            raise BusinessRuleError("A voucher has already been issued for this order.")

        voucher_code = uuid.uuid4().hex[:16].upper()
        voucher = await self._repo.create_voucher(
            order_id=order_id,
            voucher_code=voucher_code,
            issued_by=uuid.UUID(reviewer_actor.user_id),
            notes=data.notes,
        )

        await audit_mod.record_audit(
            self._session,
            event_type=AuditEventType.export_generated,
            actor_id=uuid.UUID(reviewer_actor.user_id),
            actor_role=reviewer_actor.role.value,
            resource_type="voucher",
            resource_id=str(voucher.id),
            outcome="issued",
            detail={"voucher_code": voucher_code},
        )

        return VoucherRead(
            id=voucher.id,
            order_id=voucher.order_id,
            voucher_code=voucher.voucher_code,
            issued_by=voucher.issued_by,
            issued_at=voucher.issued_at,
            notes=voucher.notes,
        )

    async def get_voucher(self, order_id: uuid.UUID, actor: Actor) -> VoucherRead | None:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        profile = await CandidateRepository(self._session).get_by_id(order.candidate_id)
        owner_user_id = str(profile.user_id) if profile else ""
        assert_roles_or_owner(actor, [UserRole.reviewer, UserRole.admin], owner_user_id)
        voucher = await self._repo.get_voucher(order_id)
        if voucher is None:
            return None
        return VoucherRead(
            id=voucher.id,
            order_id=voucher.order_id,
            voucher_code=voucher.voucher_code,
            issued_by=voucher.issued_by,
            issued_at=voucher.issued_at,
            notes=voucher.notes,
        )

    async def add_milestone(
        self,
        order_id: uuid.UUID,
        reviewer_actor: Actor,
        data: MilestoneCreate,
    ) -> MilestoneRead:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        if order.status != OrderStatus.pending_fulfillment.value:
            raise BusinessRuleError("Milestones can only be recorded for pending_fulfillment orders.")

        now = _now()
        milestone = await self._repo.add_milestone(
            order_id=order_id,
            milestone_type=data.milestone_type,
            description=data.description,
            recorded_by=uuid.UUID(reviewer_actor.user_id),
            occurred_at=now,
        )
        return MilestoneRead(
            id=milestone.id,
            order_id=milestone.order_id,
            milestone_type=milestone.milestone_type,
            description=milestone.description,
            recorded_by=milestone.recorded_by,
            occurred_at=milestone.occurred_at,
        )

    async def list_milestones(self, order_id: uuid.UUID, actor: Actor) -> list[MilestoneRead]:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        profile = await CandidateRepository(self._session).get_by_id(order.candidate_id)
        owner_user_id = str(profile.user_id) if profile else ""
        assert_roles_or_owner(actor, [UserRole.reviewer, UserRole.admin], owner_user_id)
        milestones = await self._repo.list_milestones(order_id)
        return [
            MilestoneRead(
                id=m.id,
                order_id=m.order_id,
                milestone_type=m.milestone_type,
                description=m.description,
                recorded_by=m.recorded_by,
                occurred_at=m.occurred_at,
            )
            for m in milestones
        ]
