import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.enums import AuditEventType


class AuditEventRead(BaseModel):
    id: uuid.UUID
    event_type: str
    actor_id: uuid.UUID | None
    actor_role: str | None
    resource_type: str | None
    resource_id: str | None
    occurred_at: datetime
    trace_id: str | None
    outcome: str
    detail: dict | None = None


class AuditQueryParams(BaseModel):
    event_type: AuditEventType | None = None
    actor_id: uuid.UUID | None = None
    resource_type: str | None = Field(None, max_length=100)
    resource_id: str | None = Field(None, max_length=64)
    from_date: datetime | None = None
    to_date: datetime | None = None
    outcome: str | None = Field(None, max_length=30)


class ExportCreateRequest(BaseModel):
    export_type: str = Field(..., max_length=100)
    filters: dict | None = None


class ExportJobRead(BaseModel):
    id: uuid.UUID
    requested_by: uuid.UUID
    export_type: str
    status: str
    sha256_hash: str | None
    watermark_applied: bool
    completed_at: datetime | None
    created_at: datetime


class ForecastSnapshotRead(BaseModel):
    id: uuid.UUID
    computed_at: datetime
    forecast_horizon_days: int
    request_volume_forecast: dict
    bandwidth_p50_bytes: int | None
    bandwidth_p95_bytes: int | None
    upload_volume_trend: dict | None
    input_window_days: int


class CacheHitStatRead(BaseModel):
    id: uuid.UUID
    window_start: datetime
    window_end: datetime
    asset_group: str
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate_pct: float | None
    computed_at: datetime
