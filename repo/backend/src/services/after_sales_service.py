from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.after_sales_policy import assert_within_window, compute_window_expiry
from ..domain.enums import AuditEventType, OrderStatus, UserRole
from ..persistence.repositories.candidate_repo import CandidateRepository
from ..persistence.repositories.order_repo import OrderRepository
from ..schemas.order import AfterSalesRequestCreate, AfterSalesRequestRead
from ..security import audit as audit_mod
from ..security.errors import BusinessRuleError, ResourceNotFoundError
from ..security.rbac import Actor, assert_roles_or_owner


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class AfterSalesService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = OrderRepository(session)

    async def submit(
        self,
        order_id: uuid.UUID,
        candidate_actor: Actor,
        data: AfterSalesRequestCreate,
    ) -> AfterSalesRequestRead:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        profile = await CandidateRepository(self._session).get_by_id(order.candidate_id)
        owner_user_id = str(profile.user_id) if profile else ""
        assert_roles_or_owner(candidate_actor, [], owner_user_id)
        if order.status != OrderStatus.completed.value:
            raise BusinessRuleError("After-sales requests can only be filed for completed orders.")
        if order.completed_at is None:
            raise BusinessRuleError("Order completion timestamp is missing.")

        now = _now()
        try:
            assert_within_window(order.completed_at, now)
        except Exception as exc:
            raise BusinessRuleError(str(exc)) from exc

        window_expires = compute_window_expiry(order.completed_at)
        request = await self._repo.create_after_sales(
            order_id=order_id,
            requested_by=uuid.UUID(candidate_actor.user_id),
            request_type=data.request_type,
            description=data.description,
            window_expires_at=window_expires,
        )

        await audit_mod.record_audit(
            self._session,
            event_type=AuditEventType.order_state_changed,
            actor_id=uuid.UUID(candidate_actor.user_id),
            actor_role=candidate_actor.role.value,
            resource_type="after_sales_request",
            resource_id=str(request.id),
            outcome="submitted",
            detail={"request_type": data.request_type},
        )

        return _request_to_read(request)

    async def list(
        self, order_id: uuid.UUID, actor: Actor
    ) -> list[AfterSalesRequestRead]:
        order = await self._repo.get_order(order_id)
        if order is None:
            raise ResourceNotFoundError("Order not found.")
        profile = await CandidateRepository(self._session).get_by_id(order.candidate_id)
        owner_user_id = str(profile.user_id) if profile else ""
        assert_roles_or_owner(actor, [UserRole.reviewer, UserRole.admin], owner_user_id)
        requests = await self._repo.list_after_sales(order_id)
        return [_request_to_read(r) for r in requests]

    async def resolve(
        self,
        order_id: uuid.UUID,
        request_id: uuid.UUID,
        reviewer_actor: Actor,
        resolution_notes: str,
    ) -> AfterSalesRequestRead:
        request = await self._repo.get_after_sales(request_id)
        if request is None:
            raise ResourceNotFoundError("After-sales request not found.")
        if request.order_id != order_id:
            raise ResourceNotFoundError(
                "After-sales request does not belong to this order."
            )
        if request.status == "resolved":
            raise BusinessRuleError("After-sales request is already resolved.")

        await self._repo.resolve_after_sales(
            request,
            resolved_by=uuid.UUID(reviewer_actor.user_id),
            resolution_notes=resolution_notes,
        )

        await audit_mod.record_audit(
            self._session,
            event_type=AuditEventType.order_state_changed,
            actor_id=uuid.UUID(reviewer_actor.user_id),
            actor_role=reviewer_actor.role.value,
            resource_type="after_sales_request",
            resource_id=str(request_id),
            outcome="resolved",
        )

        return _request_to_read(request)


def _request_to_read(request) -> AfterSalesRequestRead:
    return AfterSalesRequestRead(
        id=request.id,
        order_id=request.order_id,
        requested_by=request.requested_by,
        request_type=request.request_type,
        description=request.description,
        status=request.status,
        window_expires_at=request.window_expires_at,
        resolved_by=request.resolved_by,
        resolved_at=request.resolved_at,
        resolution_notes=request.resolution_notes,
        created_at=request.created_at,
    )
