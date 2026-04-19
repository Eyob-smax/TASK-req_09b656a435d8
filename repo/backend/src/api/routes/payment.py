from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from ...domain.enums import UserRole
from ...schemas.common import SuccessResponse, make_success
from ...schemas.order import (
    MilestoneCreate,
    MilestoneRead,
    PaymentConfirmRequest,
    PaymentProofSubmit,
    VoucherCreate,
    VoucherRead,
)
from ...services.order_service import OrderService
from ...services.payment_service import PaymentService
from ..dependencies import CurrentActor, DbSession, require_role, require_signed_request

router = APIRouter(prefix="/orders/{order_id}", tags=["payment"])


# 22. POST /orders/{order_id}/payment/proof — candidate submits proof
@router.post(
    "/payment/proof",
    response_model=SuccessResponse[dict],
    dependencies=[
        Depends(require_role(UserRole.candidate)),
        Depends(require_signed_request),
    ],
)
async def submit_payment_proof(
    order_id: uuid.UUID,
    data: PaymentProofSubmit,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[dict]:
    svc = PaymentService(session)
    record = await svc.submit_proof(order_id, actor, data)
    return make_success(
        {
            "order_id": str(record.order_id),
            "payment_method": record.payment_method,
            "reference_number": record.reference_number,
            "amount": str(record.amount),
            "confirmed": record.confirmed_by is not None,
        }
    )


# 23. POST /orders/{order_id}/payment/confirm — reviewer/admin confirms
@router.post(
    "/payment/confirm",
    response_model=SuccessResponse[dict],
    dependencies=[
        Depends(require_role(UserRole.reviewer, UserRole.admin)),
        Depends(require_signed_request),
    ],
)
async def confirm_payment(
    order_id: uuid.UUID,
    data: PaymentConfirmRequest,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[dict]:
    svc = PaymentService(session)
    order = await svc.confirm_payment(order_id, actor, data)
    return make_success({"order_id": str(order.id), "status": order.status.value})


# 24. POST /orders/{order_id}/voucher — reviewer/admin issues voucher
@router.post(
    "/voucher",
    response_model=SuccessResponse[VoucherRead],
    status_code=201,
    dependencies=[
        Depends(require_role(UserRole.reviewer, UserRole.admin)),
        Depends(require_signed_request),
    ],
)
async def issue_voucher(
    order_id: uuid.UUID,
    data: VoucherCreate,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[VoucherRead]:
    svc = PaymentService(session)
    voucher = await svc.issue_voucher(order_id, actor, data)
    return make_success(voucher)


# 25. GET /orders/{order_id}/voucher — auth, owner/staff
@router.get(
    "/voucher",
    response_model=SuccessResponse[VoucherRead | None],
)
async def get_voucher(
    order_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[VoucherRead | None]:
    svc = PaymentService(session)
    voucher = await svc.get_voucher(order_id, actor)
    return make_success(voucher)


# 26. POST /orders/{order_id}/milestones — reviewer/admin
@router.post(
    "/milestones",
    response_model=SuccessResponse[MilestoneRead],
    status_code=201,
    dependencies=[
        Depends(require_role(UserRole.reviewer, UserRole.admin)),
        Depends(require_signed_request),
    ],
)
async def add_milestone(
    order_id: uuid.UUID,
    data: MilestoneCreate,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[MilestoneRead]:
    svc = PaymentService(session)
    milestone = await svc.add_milestone(order_id, actor, data)
    return make_success(milestone)


# 27. GET /orders/{order_id}/milestones — auth, owner/staff
@router.get(
    "/milestones",
    response_model=SuccessResponse[list[MilestoneRead]],
)
async def list_milestones(
    order_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[list[MilestoneRead]]:
    svc = PaymentService(session)
    milestones = await svc.list_milestones(order_id, actor)
    return make_success(milestones)
