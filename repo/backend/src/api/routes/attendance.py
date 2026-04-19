from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile

from ...domain.enums import UserRole
from ...schemas.attendance import (
    AnomalyCreate,
    AnomalyRead,
    AttendanceExceptionCreate,
    ExceptionRead,
    ExceptionReviewStepRead,
    ProofUploadResponse,
    ReviewDecisionCreate,
)
from ...schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse, ApiMeta, make_success
from ...services.attendance_service import AttendanceService
from ...storage.file_store import get_file_store
from ..dependencies import CurrentActor, DbSession, require_role, require_signed_request

router = APIRouter(prefix="/attendance", tags=["attendance"])


# 39. POST /attendance/anomalies — proctor/reviewer/admin flags anomaly
@router.post(
    "/anomalies",
    response_model=SuccessResponse[AnomalyRead],
    status_code=201,
    dependencies=[Depends(require_role(UserRole.proctor, UserRole.reviewer, UserRole.admin))],
)
async def flag_anomaly(
    data: AnomalyCreate,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[AnomalyRead]:
    svc = AttendanceService(session, get_file_store())
    anomaly = await svc.flag_anomaly(actor, data)
    return make_success(anomaly)


# 40. GET /attendance/anomalies — auth, row-scoped
@router.get(
    "/anomalies",
    response_model=SuccessResponse[list[AnomalyRead]],
)
async def list_anomalies(
    session: DbSession,
    actor: CurrentActor,
    candidate_id: Optional[uuid.UUID] = Query(None),
) -> SuccessResponse[list[AnomalyRead]]:
    svc = AttendanceService(session, get_file_store())
    anomalies = await svc.list_anomalies(actor, candidate_id=candidate_id)
    return make_success(anomalies)


# 41. POST /attendance/exceptions — auth, signed, create exception
@router.post(
    "/exceptions",
    response_model=SuccessResponse[ExceptionRead],
    status_code=201,
    dependencies=[Depends(require_signed_request)],
)
async def create_exception(
    data: AttendanceExceptionCreate,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[ExceptionRead]:
    from ...persistence.repositories.candidate_repo import CandidateRepository
    from ...security.errors import ResourceNotFoundError

    candidate_repo = CandidateRepository(session)
    profile = await candidate_repo.get_by_user_id(uuid.UUID(actor.user_id))
    if profile is None:
        raise ResourceNotFoundError("Candidate profile not found. Create a profile first.")
    svc = AttendanceService(session, get_file_store())
    exc = await svc.create_exception(profile.id, actor, data)
    return make_success(exc)


# 42. GET /attendance/exceptions — auth, row-scoped, status filter
@router.get(
    "/exceptions",
    response_model=PaginatedResponse[ExceptionRead],
)
async def list_exceptions(
    session: DbSession,
    actor: CurrentActor,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ExceptionRead]:
    svc = AttendanceService(session, get_file_store())
    exceptions, total = await svc.list_exceptions(actor, status=status, page=page, page_size=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        data=exceptions,
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        meta=ApiMeta.now(),
    )


# 43. GET /attendance/exceptions/{exception_id} — auth, owner/staff
@router.get(
    "/exceptions/{exception_id}",
    response_model=SuccessResponse[ExceptionRead],
)
async def get_exception(
    exception_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[ExceptionRead]:
    svc = AttendanceService(session, get_file_store())
    exc = await svc.get_exception(exception_id, actor)
    return make_success(exc)


# 44. POST /attendance/exceptions/{exception_id}/proof — candidate, multipart
@router.post(
    "/exceptions/{exception_id}/proof",
    response_model=SuccessResponse[ProofUploadResponse],
    status_code=201,
    dependencies=[
        Depends(require_role(UserRole.candidate)),
        Depends(require_signed_request),
    ],
)
async def upload_proof(
    exception_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
    file: UploadFile = File(...),
) -> SuccessResponse[ProofUploadResponse]:
    svc = AttendanceService(session, get_file_store())
    file_bytes = await file.read()
    result = await svc.upload_proof(
        exception_id=exception_id,
        actor=actor,
        file_bytes=file_bytes,
        original_filename=file.filename or "proof",
        content_type=file.content_type or "application/octet-stream",
    )
    return make_success(result)


# 45. POST /attendance/exceptions/{exception_id}/review — proctor/reviewer/admin
@router.post(
    "/exceptions/{exception_id}/review",
    response_model=SuccessResponse[ExceptionReviewStepRead],
    dependencies=[
        Depends(require_role(UserRole.proctor, UserRole.reviewer, UserRole.admin)),
        Depends(require_signed_request),
    ],
)
async def submit_exception_review(
    exception_id: uuid.UUID,
    data: ReviewDecisionCreate,
    session: DbSession,
    actor: CurrentActor,
) -> SuccessResponse[ExceptionReviewStepRead]:
    svc = AttendanceService(session, get_file_store())
    step = await svc.submit_review(exception_id, actor, data)
    return make_success(step)
