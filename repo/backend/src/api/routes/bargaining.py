from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ...domain.enums import UserRole
from ...schemas.bargaining import (
    BargainingAcceptRequest,
    BargainingThreadRead,
    CounterAcceptRequest,
    CounterCreate,
    OfferCreate,
    OfferRead,
)
from ...schemas.common import SuccessResponse, make_success
from ...services.bargaining_service import BargainingService
from ..dependencies import CurrentActor, DbSession, require_role, require_signed_request

router = APIRouter(prefix="/orders/{order_id}/bargaining", tags=["bargaining"])


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


# 28. POST /orders/{order_id}/bargaining/offer — candidate, signed
@router.post(
    "/offer",
    response_model=SuccessResponse[OfferRead],
    status_code=201,
    dependencies=[Depends(require_role(UserRole.candidate)), Depends(require_signed_request)],
)
async def submit_offer(
    order_id: uuid.UUID,
    data: OfferCreate,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[OfferRead]:
    svc = BargainingService(session)
    now = _now()
    offer = await svc.submit_offer(order_id, actor, data.amount, now)
    return make_success(offer)


# 29. GET /orders/{order_id}/bargaining — get thread (auth, owner/staff)
@router.get(
    "",
    response_model=SuccessResponse[BargainingThreadRead],
)
async def get_bargaining_thread(
    order_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[BargainingThreadRead]:
    svc = BargainingService(session)
    thread = await svc.get_thread(order_id, actor)
    return make_success(thread)


# 30. POST /orders/{order_id}/bargaining/accept — reviewer/admin accepts offer, signed
@router.post(
    "/accept",
    response_model=SuccessResponse[BargainingThreadRead],
    dependencies=[Depends(require_role(UserRole.reviewer, UserRole.admin)), Depends(require_signed_request)],
)
async def accept_offer(
    order_id: uuid.UUID,
    data: BargainingAcceptRequest,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[BargainingThreadRead]:
    svc = BargainingService(session)
    thread = await svc.accept_offer(order_id, actor, data.offer_id, _now())
    return make_success(thread)


# 31. POST /orders/{order_id}/bargaining/counter — reviewer/admin counters, signed
@router.post(
    "/counter",
    response_model=SuccessResponse[BargainingThreadRead],
    dependencies=[Depends(require_role(UserRole.reviewer, UserRole.admin)), Depends(require_signed_request)],
)
async def counter_offer(
    order_id: uuid.UUID,
    data: CounterCreate,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[BargainingThreadRead]:
    svc = BargainingService(session)
    thread = await svc.counter_offer(order_id, actor, data.counter_amount, _now())
    return make_success(thread)


# 32. POST /orders/{order_id}/bargaining/accept-counter — candidate, signed
@router.post(
    "/accept-counter",
    response_model=SuccessResponse[BargainingThreadRead],
    dependencies=[Depends(require_role(UserRole.candidate)), Depends(require_signed_request)],
)
async def accept_counter(
    order_id: uuid.UUID,
    data: CounterAcceptRequest,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[BargainingThreadRead]:
    svc = BargainingService(session)
    thread = await svc.accept_counter(order_id, actor, _now())
    return make_success(thread)
