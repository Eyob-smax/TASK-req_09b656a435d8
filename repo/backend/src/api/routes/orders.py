from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ...domain.enums import OrderStatus, UserRole
from ...schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse, ApiMeta, make_success
from ...schemas.order import (
    OrderCreate,
    OrderRead,
    OrderTransitionRequest,
    ServiceItemRead,
)
from ...services.idempotency import IdempotencyStore
from ...services.order_service import OrderService
from ..dependencies import (
    CurrentActor,
    DbSession,
    IdempotencyKeyHeader,
    require_role,
    require_signed_request,
)

router = APIRouter(tags=["orders"])


# 15. GET /services — public catalog (auth)
@router.get(
    "/services",
    response_model=SuccessResponse[list[ServiceItemRead]],
)
async def list_service_items(
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[list[ServiceItemRead]]:
    svc = OrderService(session)
    items = await svc.list_service_items()
    return make_success(items)


# 16. POST /orders — create order (candidate, signed, Idempotency-Key).
# Idempotency contract (per docs/api-spec.md §5): (key, method, path) is unique;
# a repeat with the same body replays the cached envelope verbatim; a repeat
# with a different body raises IdempotencyConflictError → 409 IDEMPOTENCY_CONFLICT.
# The raw request body is hashed here (before service execution) so a header-only
# retry collapses to one DB write.
@router.post(
    "/orders",
    response_model=SuccessResponse[OrderRead],
    status_code=201,
    dependencies=[Depends(require_role(UserRole.candidate)), Depends(require_signed_request)],
)
async def create_order(
    data: OrderCreate,
    request: Request,
    session: DbSession,
    actor: CurrentActor,
    idempotency_key: IdempotencyKeyHeader = None,
):
    raw_body = await request.body()
    store = IdempotencyStore(session)

    if idempotency_key:
        cached = await store.fetch(
            key=idempotency_key,
            method="POST",
            path="/api/v1/orders",
            request_body=raw_body,
        )
        if cached is not None:
            return JSONResponse(status_code=cached.status_code, content=cached.body)
        if not data.idempotency_key:
            data = data.model_copy(update={"idempotency_key": idempotency_key})

    svc = OrderService(session)
    order = await svc.create_order(actor, data)
    envelope = make_success(order)
    envelope_json = jsonable_encoder(envelope.model_dump(mode="json"))

    if idempotency_key:
        await store.store(
            key=idempotency_key,
            method="POST",
            path="/api/v1/orders",
            actor_id=uuid.UUID(actor.user_id),
            request_body=raw_body,
            response_status=201,
            response_body=envelope_json,
        )

    return JSONResponse(status_code=201, content=envelope_json)


# 17. GET /orders — list (auth, row-scoped, status filter)
@router.get(
    "/orders",
    response_model=PaginatedResponse[OrderRead],
)
async def list_orders(
    session: DbSession,
    actor: CurrentActor,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[OrderRead]:
    svc = OrderService(session)
    orders, total = await svc.list_orders(actor, status=status, page=page, page_size=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        data=orders,
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        meta=ApiMeta.now(),
    )


# 18. GET /orders/{order_id} — get (auth, owner/staff)
@router.get(
    "/orders/{order_id}",
    response_model=SuccessResponse[OrderRead],
)
async def get_order(
    order_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[OrderRead]:
    svc = OrderService(session)
    order = await svc.get_order(order_id, actor)
    return make_success(order)


# 19. POST /orders/{order_id}/cancel — cancel (auth, owner/staff, signed)
@router.post(
    "/orders/{order_id}/cancel",
    response_model=SuccessResponse[OrderRead],
    dependencies=[Depends(require_signed_request)],
)
async def cancel_order(
    order_id: uuid.UUID,
    data: OrderTransitionRequest,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[OrderRead]:
    svc = OrderService(session)
    order = await svc.cancel(order_id, actor, reason=data.notes or "")
    return make_success(order)


# 20. POST /orders/{order_id}/confirm-receipt — candidate only, signed
@router.post(
    "/orders/{order_id}/confirm-receipt",
    response_model=SuccessResponse[OrderRead],
    dependencies=[Depends(require_role(UserRole.candidate)), Depends(require_signed_request)],
)
async def confirm_receipt(
    order_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[OrderRead]:
    svc = OrderService(session)
    order = await svc.confirm_receipt(order_id, actor)
    return make_success(order)


# 21. POST /orders/{order_id}/advance — reviewer/admin, signed
@router.post(
    "/orders/{order_id}/advance",
    response_model=SuccessResponse[OrderRead],
    dependencies=[Depends(require_role(UserRole.reviewer, UserRole.admin)), Depends(require_signed_request)],
)
async def advance_order(
    order_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[OrderRead]:
    svc = OrderService(session)
    order = await svc.advance_to_receipt(order_id, actor)
    return make_success(order)
