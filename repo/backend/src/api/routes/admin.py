"""
Admin API routes — system administrator surfaces for:
  - Feature flag management
  - Cohort definition and canary assignment
  - Audit log search
  - RBAC / masking policy inspection
  - Export job creation and download
  - Metrics summary, cache stats, access log summaries
  - Forecast snapshots
  - Per-user config bootstrap (canary routing decision)

All routes require admin role.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from ...domain.enums import UserRole
from ...schemas.audit import (
    AuditEventRead,
    AuditQueryParams,
    CacheHitStatRead,
    ExportCreateRequest,
    ExportJobRead,
    ForecastSnapshotRead,
)
from ...schemas.common import PaginatedResponse, PaginationMeta, ApiMeta, SuccessResponse, make_success
from ...schemas.config import (
    BootstrapConfigResponse,
    CohortAssignmentCreate,
    CohortDefinitionCreate,
    CohortDefinitionRead,
    FeatureFlagRead,
    FeatureFlagUpdate,
)
from ...services.config_service import ConfigService
from ...services.export_service import ExportService
from ...services.forecasting_service import ForecastingService
from ...services.telemetry_service import TelemetryService
from ..dependencies import CurrentActor, DbSession, require_role

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.admin))],
)

# ── Feature flags ─────────────────────────────────────────────────────────────

@router.get("/feature-flags", response_model=SuccessResponse[list[FeatureFlagRead]])
async def list_feature_flags(session: DbSession, actor: CurrentActor):
    svc = ConfigService(session)
    flags = await svc.list_flags()
    return make_success(flags)


@router.post("/feature-flags", response_model=SuccessResponse[FeatureFlagRead], status_code=201)
async def create_feature_flag(
    body: FeatureFlagUpdate,
    session: DbSession,
    actor: CurrentActor,
    key: str = Query(..., max_length=100),
    description: Optional[str] = Query(None),
):
    svc = ConfigService(session)
    flag = await svc.create_flag(
        key=key,
        value=body.value,
        description=description,
        actor=actor,
    )
    return make_success(flag)


@router.patch("/feature-flags/{key}", response_model=SuccessResponse[FeatureFlagRead])
async def update_feature_flag(
    key: str,
    body: FeatureFlagUpdate,
    session: DbSession,
    actor: CurrentActor,
):
    svc = ConfigService(session)
    flag = await svc.set_flag(key, body.value, actor, change_reason=body.change_reason)
    return make_success(flag)


# ── Cohorts ───────────────────────────────────────────────────────────────────

@router.get("/cohorts", response_model=SuccessResponse[list[CohortDefinitionRead]])
async def list_cohorts(session: DbSession, actor: CurrentActor):
    svc = ConfigService(session)
    cohorts = await svc.list_cohorts()
    return make_success(cohorts)


@router.post("/cohorts", response_model=SuccessResponse[CohortDefinitionRead], status_code=201)
async def create_cohort(
    body: CohortDefinitionCreate,
    session: DbSession,
    actor: CurrentActor,
):
    svc = ConfigService(session)
    cohort = await svc.create_cohort(actor, body)
    return make_success(cohort)


@router.post("/cohorts/{cohort_id}/assign", response_model=SuccessResponse[dict])
async def assign_user_to_cohort(
    cohort_id: uuid.UUID,
    body: CohortAssignmentCreate,
    session: DbSession,
    actor: CurrentActor,
):
    svc = ConfigService(session)
    result = await svc.assign_user_cohort(cohort_id, body.user_id, actor)
    return make_success(result)


@router.delete("/cohorts/{cohort_id}/users/{user_id}", response_model=SuccessResponse[dict])
async def remove_user_from_cohort(
    cohort_id: uuid.UUID,
    user_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
):
    svc = ConfigService(session)
    await svc.remove_user_cohort(cohort_id, user_id, actor)
    return make_success({"removed": True, "user_id": str(user_id)})


# ── Bootstrap / canary routing ────────────────────────────────────────────────

@router.get("/config/bootstrap/{user_id}", response_model=SuccessResponse[BootstrapConfigResponse])
async def get_bootstrap_config(
    user_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
):
    """Return the resolved feature-flag set for a specific user (shows canary routing effect)."""
    from ...persistence.repositories.auth_repo import AuthRepository
    from ...security.errors import ResourceNotFoundError
    auth_repo = AuthRepository(session)
    user = await auth_repo.get_user_by_id(user_id)
    if user is None:
        raise ResourceNotFoundError("User not found.")
    svc = ConfigService(session)
    config = await svc.bootstrap_config(user_id, user.role)
    return make_success(config)


# ── Audit search ──────────────────────────────────────────────────────────────

@router.get("/audit", response_model=PaginatedResponse[AuditEventRead])
async def search_audit(
    session: DbSession,
    actor: CurrentActor,
    event_type: Optional[str] = Query(None),
    actor_id: Optional[uuid.UUID] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    from datetime import datetime, timezone
    from ...persistence.repositories.config_repo import ConfigRepository

    def _parse_dt(s: str | None):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None

    repo = ConfigRepository(session)
    rows, total = await repo.search_audit(
        event_type=event_type,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        from_date=_parse_dt(from_date),
        to_date=_parse_dt(to_date),
        outcome=outcome,
        page=page,
        page_size=page_size,
    )
    items = [
        AuditEventRead(
            id=r.id,
            event_type=r.event_type,
            actor_id=r.actor_id,
            actor_role=r.actor_role,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            occurred_at=r.occurred_at,
            trace_id=r.trace_id,
            outcome=r.outcome,
            detail=r.detail,
        )
        for r in rows
    ]
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        data=items,
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        meta=ApiMeta.now(),
    )


# ── RBAC / policy inspection ──────────────────────────────────────────────────

@router.get("/rbac-policy", response_model=SuccessResponse[dict])
async def get_rbac_policy(actor: CurrentActor):
    """Expose the static RBAC role-permission matrix for admin inspection."""
    from ...security.rbac import DOWNLOAD_APPROVED_ROLES, PRIVILEGED_ROLES
    from ...domain.enums import UserRole
    policy = {
        "roles": [r.value for r in UserRole],
        "download_approved_roles": [r.value for r in DOWNLOAD_APPROVED_ROLES],
        "privileged_roles": [r.value for r in PRIVILEGED_ROLES],
        "route_restrictions": {
            "reviewer_or_admin_only": [
                "GET /api/v1/queue/*",
                "POST /api/v1/documents/{id}/review",
                "GET /api/v1/documents/{id}/download",
                "POST /api/v1/orders/{id}/payment/confirm",
                "POST /api/v1/orders/{id}/advance",
                "POST /api/v1/orders/{id}/voucher",
                "POST /api/v1/orders/{id}/refund",
            ],
            "admin_only": [
                "POST /api/v1/orders/{id}/refund/process",
                "GET /api/v1/admin/*",
            ],
            "candidate_only": [
                "POST /api/v1/orders/{id}/confirm-receipt",
                "POST /api/v1/orders/{id}/payment/proof",
                "POST /api/v1/orders/{id}/bargaining/offer",
                "POST /api/v1/orders/{id}/bargaining/accept-counter",
            ],
        },
    }
    return make_success(policy)


@router.get("/masking-policy", response_model=SuccessResponse[dict])
async def get_masking_policy(actor: CurrentActor):
    """Expose column-level masking rules for admin inspection."""
    policy = {
        "masked_fields": {
            "candidate_profiles.ssn": {
                "mask": "***-**-{last4}",
                "visible_to": ["reviewer", "admin"],
            },
            "candidate_profiles.date_of_birth": {
                "mask": "{year}-**-**",
                "visible_to": ["reviewer", "admin"],
            },
            "candidate_profiles.phone_number": {
                "mask": "***-***-{last4}",
                "visible_to": ["reviewer", "admin"],
            },
            "candidate_profiles.email": {
                "mask": "***@{domain}",
                "visible_to": ["reviewer", "admin"],
            },
        },
        "restricted_downloads": {
            "documents": {
                "allowed_roles": ["reviewer", "admin"],
                "watermark_applied": True,
                "sha256_verified": True,
            },
            "exports": {
                "allowed_roles": ["admin"],
                "watermark_applied": True,
                "sha256_stored": True,
            },
        },
    }
    return make_success(policy)


# ── Exports ───────────────────────────────────────────────────────────────────

@router.post("/exports", response_model=SuccessResponse[ExportJobRead], status_code=201)
async def create_export(
    body: ExportCreateRequest,
    session: DbSession,
    actor: CurrentActor,
):
    svc = ExportService(session)
    job = await svc.create_export_job(actor, body.export_type, body.filters)
    return make_success(job)


@router.get("/exports", response_model=PaginatedResponse[ExportJobRead])
async def list_exports(
    session: DbSession,
    actor: CurrentActor,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    svc = ExportService(session)
    jobs, total = await svc.list_export_jobs(actor, page=page, page_size=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        data=jobs,
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        meta=ApiMeta.now(),
    )


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: uuid.UUID,
    session: DbSession,
    actor: CurrentActor,
):
    svc = ExportService(session)
    content, disposition = await svc.download_export(export_id, actor)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": disposition},
    )


# ── Metrics / observability ───────────────────────────────────────────────────

@router.get("/metrics/summary", response_model=SuccessResponse[dict])
async def get_metrics_summary(session: DbSession, actor: CurrentActor):
    svc = TelemetryService(session)
    summary = svc.get_metrics_summary()
    return make_success(summary)


@router.get("/traces", response_model=PaginatedResponse[dict])
async def list_traces(
    session: DbSession,
    actor: CurrentActor,
    trace_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    svc = TelemetryService(session)
    items, total = await svc.list_trace_records(trace_id=trace_id, page=page, page_size=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        data=items,
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        meta=ApiMeta.now(),
    )


@router.get("/cache-stats", response_model=PaginatedResponse[CacheHitStatRead])
async def get_cache_stats(
    session: DbSession,
    actor: CurrentActor,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    svc = TelemetryService(session)
    items, total = await svc.list_cache_stats(page=page, page_size=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        data=items,
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        meta=ApiMeta.now(),
    )


@router.get("/access-logs", response_model=PaginatedResponse[dict])
async def get_access_log_summaries(
    session: DbSession,
    actor: CurrentActor,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    svc = TelemetryService(session)
    items, total = await svc.list_access_summaries(page=page, page_size=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        data=items,
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        meta=ApiMeta.now(),
    )


# ── Forecasts ─────────────────────────────────────────────────────────────────

@router.get("/forecasts", response_model=PaginatedResponse[ForecastSnapshotRead])
async def list_forecasts(
    session: DbSession,
    actor: CurrentActor,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    svc = ForecastingService(session)
    items, total = await svc.list_forecasts(page=page, page_size=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        data=items,
        pagination=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
        meta=ApiMeta.now(),
    )


@router.post("/forecasts/compute", response_model=SuccessResponse[ForecastSnapshotRead], status_code=201)
async def trigger_forecast(
    session: DbSession,
    actor: CurrentActor,
    horizon_days: int = Query(30, ge=1, le=365),
    input_window_days: int = Query(90, ge=7, le=365),
):
    """Manually trigger a forecast computation (also runs automatically hourly)."""
    svc = ForecastingService(session)
    snap = await svc.compute_forecast(
        horizon_days=horizon_days, input_window_days=input_window_days
    )
    return make_success(snap)
