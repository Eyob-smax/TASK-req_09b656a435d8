import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FeatureFlag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feature_flags"
    __table_args__ = (
        UniqueConstraint("key", name="uq_feature_flag_key"),
    )

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), default="boolean", nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    history: Mapped[list["FeatureFlagHistory"]] = relationship(back_populates="flag")


class FeatureFlagHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "feature_flag_history"
    __table_args__ = (
        Index("ix_flag_history_flag_id", "flag_id"),
    )

    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("feature_flags.id", ondelete="CASCADE"), nullable=False
    )
    flag_key: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    change_reason: Mapped[str | None] = mapped_column(String(500))

    flag: Mapped["FeatureFlag"] = relationship(back_populates="history")


class CohortDefinition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cohort_definitions"
    __table_args__ = (
        UniqueConstraint("cohort_key", name="uq_cohort_key"),
    )

    cohort_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    flag_overrides: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    assignments: Mapped[list["CanaryAssignment"]] = relationship(back_populates="cohort")


class CanaryAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "canary_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "cohort_id", name="uq_canary_user_cohort"),
        Index("ix_canary_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohort_definitions.id", ondelete="CASCADE"), nullable=False
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    cohort: Mapped["CohortDefinition"] = relationship(back_populates="assignments")


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_event_type", "event_type"),
        Index("ix_audit_events_actor_id", "actor_id"),
        Index("ix_audit_events_occurred_at", "occurred_at"),
        Index("ix_audit_events_resource_type_id", "resource_type", "resource_id"),
    )

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor_role: Mapped[str | None] = mapped_column(String(20))
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(64))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSONB)


class ExportJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "export_jobs"
    __table_args__ = (
        Index("ix_export_jobs_requested_by", "requested_by"),
    )

    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    export_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    storage_path: Mapped[str | None] = mapped_column(Text)
    sha256_hash: Mapped[str | None] = mapped_column(String(64))
    watermark_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    watermark_username: Mapped[str | None] = mapped_column(String(150))
    watermark_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)


class AccessLogSummary(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "access_log_summaries"
    __table_args__ = (
        UniqueConstraint("window_start", "endpoint_group", name="uq_access_log_window_group"),
        Index("ix_access_log_window_start", "window_start"),
    )

    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    endpoint_group: Mapped[str] = mapped_column(String(100), nullable=False)
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    p50_latency_ms: Mapped[int | None] = mapped_column(Integer)
    p95_latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CacheHitStat(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "cache_hit_stats"
    __table_args__ = (
        UniqueConstraint("window_start", "asset_group", name="uq_cache_stat_window_group"),
        Index("ix_cache_hit_stats_window_start", "window_start"),
    )

    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    asset_group: Mapped[str] = mapped_column(String(100), nullable=False)
    total_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    cache_hits: Mapped[int] = mapped_column(Integer, nullable=False)
    cache_misses: Mapped[int] = mapped_column(Integer, nullable=False)
    hit_rate_pct: Mapped[float | None] = mapped_column()
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ForecastSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "forecast_snapshots"
    __table_args__ = (
        Index("ix_forecast_snapshots_computed_at", "computed_at"),
    )

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    request_volume_forecast: Mapped[dict] = mapped_column(JSONB, nullable=False)
    bandwidth_p50_bytes: Mapped[int | None] = mapped_column(BigInteger)
    bandwidth_p95_bytes: Mapped[int | None] = mapped_column(BigInteger)
    upload_volume_trend: Mapped[dict | None] = mapped_column(JSONB)
    input_window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class TelemetryCorrelation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "telemetry_correlations"
    __table_args__ = (
        Index("ix_telemetry_trace_id", "trace_id"),
        Index("ix_telemetry_occurred_at", "occurred_at"),
    )

    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    span_id: Mapped[str | None] = mapped_column(String(32))
    operation: Mapped[str] = mapped_column(String(200), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSONB)
