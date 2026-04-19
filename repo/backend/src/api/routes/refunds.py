from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from ...domain.enums import UserRole
from ...schemas.common import SuccessResponse, make_success
from ...schemas.order import (
    AfterSalesRequestCreate,
    AfterSalesRequestRead,
    AfterSalesResolveRequest,
    RefundCreate,
    RefundRead,
)
from ...services.after_sales_service import AfterSalesService
from ...services.refund_service import RefundService
from ..dependencies import CurrentActor, DbSession, require_role, require_signed_request

router = APIRouter(prefix="/orders/{order_id}", tags=["refunds"])


# 33. POST /orders/{order_id}/refund — reviewer initiates refund
@router.post(
    "/refund",
    response_model=SuccessResponse[RefundRead],
    status_code=201,
    dependencies=[
        Depends(require_role(UserRole.reviewer, UserRole.admin)),
        Depends(require_signed_request),
    ],
)
async def initiate_refund(
    order_id: uuid.UUID,
    data: RefundCreate,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[RefundRead]:
    svc = RefundService(session)
    refund = await svc.initiate_refund(order_id, actor, data)
    return make_success(refund)


# 34. POST /orders/{order_id}/refund/process — admin processes refund
@router.post(
    "/refund/process",
    response_model=SuccessResponse[RefundRead],
    dependencies=[
        Depends(require_role(UserRole.admin)),
        Depends(require_signed_request),
    ],
)
async def process_refund(
    order_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[RefundRead]:
    svc = RefundService(session)
    refund = await svc.process_refund(order_id, actor)
    return make_success(refund)


# 35. GET /orders/{order_id}/refund — auth, owner/staff
@router.get(
    "/refund",
    response_model=SuccessResponse[RefundRead | None],
)
async def get_refund(
    order_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[RefundRead | None]:
    svc = RefundService(session)
    refund = await svc.get_refund(order_id, actor)
    return make_success(refund)


# 36. POST /orders/{order_id}/after-sales — candidate, 14-day window
@router.post(
    "/after-sales",
    response_model=SuccessResponse[AfterSalesRequestRead],
    status_code=201,
    dependencies=[
        Depends(require_role(UserRole.candidate)),
        Depends(require_signed_request),
    ],
)
async def submit_after_sales(
    order_id: uuid.UUID,
    data: AfterSalesRequestCreate,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[AfterSalesRequestRead]:
    svc = AfterSalesService(session)
    request = await svc.submit(order_id, actor, data)
    return make_success(request)


# 37. GET /orders/{order_id}/after-sales — auth, owner/staff
@router.get(
    "/after-sales",
    response_model=SuccessResponse[list[AfterSalesRequestRead]],
)
async def list_after_sales(
    order_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[list[AfterSalesRequestRead]]:
    svc = AfterSalesService(session)
    requests = await svc.list(order_id, actor)
    return make_success(requests)


# 38. POST /orders/{order_id}/after-sales/{request_id}/resolve — reviewer/admin
@router.post(
    "/after-sales/{request_id}/resolve",
    response_model=SuccessResponse[AfterSalesRequestRead],
    dependencies=[
        Depends(require_role(UserRole.reviewer, UserRole.admin)),
        Depends(require_signed_request),
    ],
)
async def resolve_after_sales(
    order_id: uuid.UUID,
    request_id: uuid.UUID,
    data: AfterSalesResolveRequest,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[AfterSalesRequestRead]:
    svc = AfterSalesService(session)
    request = await svc.resolve(order_id, request_id, actor, data.resolution_notes)
    return make_success(request)
