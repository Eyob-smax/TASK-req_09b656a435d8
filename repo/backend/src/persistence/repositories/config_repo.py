"""
Repository for config/admin tables: FeatureFlag, CohortDefinition, CanaryAssignment,
AuditEvent, ExportJob, ForecastSnapshot, CacheHitStat, AccessLogSummary, TelemetryCorrelation.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.config_audit import (
    AccessLogSummary,
    AuditEvent,
    CacheHitStat,
    CanaryAssignment,
    CohortDefinition,
    ExportJob,
    FeatureFlag,
    FeatureFlagHistory,
    ForecastSnapshot,
    TelemetryCorrelation,
)


class ConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Feature flags ────────────────────────────────────────────────────
    async def get_flag(self, key: str) -> FeatureFlag | None:
        q = select(FeatureFlag).where(FeatureFlag.key == key)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_flags(self) -> list[FeatureFlag]:
        q = select(FeatureFlag).order_by(FeatureFlag.key)
        return list((await self.session.execute(q)).scalars().all())

    async def create_flag(
        self,
        *,
        key: str,
        value: str,
        value_type: str = "boolean",
        description: str | None = None,
        updated_by: uuid.UUID | None = None,
    ) -> FeatureFlag:
        flag = FeatureFlag(
            key=key,
            value=value,
            value_type=value_type,
            description=description,
            updated_by=updated_by,
        )
        self.session.add(flag)
        await self.session.flush()
        return flag

    async def update_flag(
        self,
        flag: FeatureFlag,
        *,
        new_value: str,
        changed_by: uuid.UUID,
        change_reason: str | None = None,
        now: datetime | None = None,
    ) -> FeatureFlagHistory:
        from datetime import timezone
        ts = now or datetime.now(tz=timezone.utc)
        history = FeatureFlagHistory(
            flag_id=flag.id,
            flag_key=flag.key,
            old_value=flag.value,
            new_value=new_value,
            changed_by=changed_by,
            changed_at=ts,
            change_reason=change_reason,
        )
        self.session.add(history)
        flag.value = new_value
        flag.updated_by = changed_by
        await self.session.flush()
        await self.session.refresh(flag)
        return history

    async def list_flag_history(self, flag_id: uuid.UUID) -> list[FeatureFlagHistory]:
        q = select(FeatureFlagHistory).where(FeatureFlagHistory.flag_id == flag_id).order_by(
            FeatureFlagHistory.changed_at.desc()
        )
        return list((await self.session.execute(q)).scalars().all())

    # ── Cohort definitions ────────────────────────────────────────────────
    async def get_cohort(self, cohort_id: uuid.UUID) -> CohortDefinition | None:
        return await self.session.get(CohortDefinition, cohort_id)

    async def get_cohort_by_key(self, cohort_key: str) -> CohortDefinition | None:
        q = select(CohortDefinition).where(CohortDefinition.cohort_key == cohort_key)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_cohorts(self, active_only: bool = False) -> list[CohortDefinition]:
        q = select(CohortDefinition)
        if active_only:
            q = q.where(CohortDefinition.is_active.is_(True))
        q = q.order_by(CohortDefinition.cohort_key)
        return list((await self.session.execute(q)).scalars().all())

    async def create_cohort(
        self,
        *,
        cohort_key: str,
        name: str,
        description: str | None = None,
        flag_overrides: dict | None = None,
        created_by: uuid.UUID | None = None,
    ) -> CohortDefinition:
        cohort = CohortDefinition(
            cohort_key=cohort_key,
            name=name,
            description=description,
            flag_overrides=flag_overrides,
            is_active=True,
            created_by=created_by,
        )
        self.session.add(cohort)
        await self.session.flush()
        return cohort

    # ── Canary assignments ────────────────────────────────────────────────
    async def get_user_assignment(self, user_id: uuid.UUID) -> CanaryAssignment | None:
        q = select(CanaryAssignment).where(CanaryAssignment.user_id == user_id)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_cohort_assignments(
        self, cohort_id: uuid.UUID
    ) -> list[CanaryAssignment]:
        q = select(CanaryAssignment).where(CanaryAssignment.cohort_id == cohort_id)
        return list((await self.session.execute(q)).scalars().all())

    async def assign_user(
        self,
        *,
        user_id: uuid.UUID,
        cohort_id: uuid.UUID,
        assigned_by: uuid.UUID | None = None,
    ) -> CanaryAssignment:
        existing = await self.get_user_assignment(user_id)
        if existing is not None:
            existing.cohort_id = cohort_id
            existing.assigned_by = assigned_by
            await self.session.flush()
            return existing
        assignment = CanaryAssignment(
            user_id=user_id,
            cohort_id=cohort_id,
            assigned_by=assigned_by,
        )
        self.session.add(assignment)
        await self.session.flush()
        return assignment

    async def remove_user_assignment(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(CanaryAssignment).where(CanaryAssignment.user_id == user_id)
        )

    # ── Audit events ─────────────────────────────────────────────────────
    async def search_audit(
        self,
        *,
        event_type: str | None = None,
        actor_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        outcome: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditEvent], int]:
        q = select(AuditEvent)
        if event_type:
            q = q.where(AuditEvent.event_type == event_type)
        if actor_id:
            q = q.where(AuditEvent.actor_id == actor_id)
        if resource_type:
            q = q.where(AuditEvent.resource_type == resource_type)
        if resource_id:
            q = q.where(AuditEvent.resource_id == resource_id)
        if from_date:
            q = q.where(AuditEvent.occurred_at >= from_date)
        if to_date:
            q = q.where(AuditEvent.occurred_at <= to_date)
        if outcome:
            q = q.where(AuditEvent.outcome == outcome)
        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.session.execute(count_q)).scalar_one()
        q = q.order_by(AuditEvent.occurred_at.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)
        rows = list((await self.session.execute(q)).scalars().all())
        return rows, total

    # ── Export jobs ───────────────────────────────────────────────────────
    async def create_export_job(
        self,
        *,
        requested_by: uuid.UUID,
        export_type: str,
    ) -> ExportJob:
        job = ExportJob(
            requested_by=requested_by,
            export_type=export_type,
            status="pending",
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def update_export_job(
        self,
        job: ExportJob,
        *,
        status: str,
        storage_path: str | None = None,
        sha256_hash: str | None = None,
        watermark_applied: bool = False,
        watermark_username: str | None = None,
        watermark_timestamp: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> None:
        job.status = status
        if storage_path is not None:
            job.storage_path = storage_path
        if sha256_hash is not None:
            job.sha256_hash = sha256_hash
        if watermark_applied:
            job.watermark_applied = True
            job.watermark_username = watermark_username
            job.watermark_timestamp = watermark_timestamp
        if completed_at is not None:
            job.completed_at = completed_at
        if error_message is not None:
            job.error_message = error_message
        await self.session.flush()

    async def get_export_job(self, job_id: uuid.UUID) -> ExportJob | None:
        return await self.session.get(ExportJob, job_id)

    async def list_export_jobs(
        self,
        *,
        requested_by: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ExportJob], int]:
        q = select(ExportJob)
        if requested_by is not None:
            q = q.where(ExportJob.requested_by == requested_by)
        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.session.execute(count_q)).scalar_one()
        q = q.order_by(ExportJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = list((await self.session.execute(q)).scalars().all())
        return rows, total

    # ── Forecast snapshots ────────────────────────────────────────────────
    async def create_forecast_snapshot(
        self,
        *,
        computed_at: datetime,
        forecast_horizon_days: int,
        request_volume_forecast: dict,
        bandwidth_p50_bytes: int | None,
        bandwidth_p95_bytes: int | None,
        upload_volume_trend: dict | None,
        input_window_days: int,
        notes: str | None = None,
    ) -> ForecastSnapshot:
        snap = ForecastSnapshot(
            computed_at=computed_at,
            forecast_horizon_days=forecast_horizon_days,
            request_volume_forecast=request_volume_forecast,
            bandwidth_p50_bytes=bandwidth_p50_bytes,
            bandwidth_p95_bytes=bandwidth_p95_bytes,
            upload_volume_trend=upload_volume_trend,
            input_window_days=input_window_days,
            notes=notes,
        )
        self.session.add(snap)
        await self.session.flush()
        return snap

    async def list_forecast_snapshots(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[ForecastSnapshot], int]:
        q = select(ForecastSnapshot)
        total = (await self.session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        q = q.order_by(ForecastSnapshot.computed_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = list((await self.session.execute(q)).scalars().all())
        return rows, total

    async def get_latest_forecast(self) -> ForecastSnapshot | None:
        q = select(ForecastSnapshot).order_by(ForecastSnapshot.computed_at.desc()).limit(1)
        return (await self.session.execute(q)).scalar_one_or_none()

    # ── Cache hit stats ───────────────────────────────────────────────────
    async def upsert_cache_stat(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        asset_group: str,
        total_requests: int,
        cache_hits: int,
        cache_misses: int,
        computed_at: datetime,
    ) -> CacheHitStat:
        q = select(CacheHitStat).where(
            CacheHitStat.window_start == window_start,
            CacheHitStat.asset_group == asset_group,
        )
        existing = (await self.session.execute(q)).scalar_one_or_none()
        hit_rate = (cache_hits / total_requests * 100.0) if total_requests > 0 else None
        if existing is not None:
            existing.total_requests = total_requests
            existing.cache_hits = cache_hits
            existing.cache_misses = cache_misses
            existing.hit_rate_pct = hit_rate
            existing.computed_at = computed_at
            await self.session.flush()
            return existing
        stat = CacheHitStat(
            window_start=window_start,
            window_end=window_end,
            asset_group=asset_group,
            total_requests=total_requests,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate_pct=hit_rate,
            computed_at=computed_at,
        )
        self.session.add(stat)
        await self.session.flush()
        return stat

    async def list_cache_stats(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[CacheHitStat], int]:
        q = select(CacheHitStat)
        total = (await self.session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        q = q.order_by(CacheHitStat.window_start.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = list((await self.session.execute(q)).scalars().all())
        return rows, total

    # ── Access log summaries ──────────────────────────────────────────────
    async def upsert_access_log_summary(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
        endpoint_group: str,
        total_requests: int,
        p50_latency_ms: int | None,
        p95_latency_ms: int | None,
        error_count: int,
        computed_at: datetime,
    ) -> AccessLogSummary:
        q = select(AccessLogSummary).where(
            AccessLogSummary.window_start == window_start,
            AccessLogSummary.endpoint_group == endpoint_group,
        )
        existing = (await self.session.execute(q)).scalar_one_or_none()
        if existing is not None:
            existing.total_requests = total_requests
            existing.p50_latency_ms = p50_latency_ms
            existing.p95_latency_ms = p95_latency_ms
            existing.error_count = error_count
            existing.computed_at = computed_at
            await self.session.flush()
            return existing
        row = AccessLogSummary(
            window_start=window_start,
            window_end=window_end,
            endpoint_group=endpoint_group,
            total_requests=total_requests,
            p50_latency_ms=p50_latency_ms,
            p95_latency_ms=p95_latency_ms,
            error_count=error_count,
            computed_at=computed_at,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_access_log_summaries(
        self,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AccessLogSummary], int]:
        q = select(AccessLogSummary)
        if from_date:
            q = q.where(AccessLogSummary.window_start >= from_date)
        if to_date:
            q = q.where(AccessLogSummary.window_end <= to_date)
        total = (await self.session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        q = q.order_by(AccessLogSummary.window_start.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = list((await self.session.execute(q)).scalars().all())
        return rows, total

    # ── Telemetry correlations ────────────────────────────────────────────
    async def list_telemetry(
        self,
        *,
        trace_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TelemetryCorrelation], int]:
        q = select(TelemetryCorrelation)
        if trace_id:
            q = q.where(TelemetryCorrelation.trace_id == trace_id)
        total = (await self.session.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        q = q.order_by(TelemetryCorrelation.occurred_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = list((await self.session.execute(q)).scalars().all())
        return rows, total
