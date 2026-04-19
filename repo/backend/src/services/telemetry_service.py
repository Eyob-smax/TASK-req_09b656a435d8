"""
Telemetry service: metrics summary, trace record lookup, access log summaries,
cache-hit stats — all local, no external SaaS.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..persistence.repositories.config_repo import ConfigRepository
from ..schemas.audit import CacheHitStatRead, ForecastSnapshotRead
from ..telemetry.metrics import registry


def _cache_stat_to_schema(row) -> CacheHitStatRead:
    return CacheHitStatRead(
        id=row.id,
        window_start=row.window_start,
        window_end=row.window_end,
        asset_group=row.asset_group,
        total_requests=row.total_requests,
        cache_hits=row.cache_hits,
        cache_misses=row.cache_misses,
        hit_rate_pct=row.hit_rate_pct,
        computed_at=row.computed_at,
    )


class TelemetryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ConfigRepository(session)

    def get_metrics_summary(self) -> dict:
        """Read live counters from the in-process MetricsRegistry and return a dict summary."""
        with registry._lock:
            metrics = dict(registry._metrics)

        summary: dict = {}
        for name, metric in metrics.items():
            from ..telemetry.metrics import Counter, Histogram
            if isinstance(metric, Counter):
                with metric._lock:
                    total = sum(metric._values.values())
                summary[name] = {"type": "counter", "total": total, "by_label": {
                    str(k): v for k, v in metric._values.items()
                }}
            elif isinstance(metric, Histogram):
                with metric._lock:
                    total_obs = sum(metric._totals.values())
                    total_sum = sum(metric._sums.values())
                summary[name] = {
                    "type": "histogram",
                    "observations": total_obs,
                    "sum": total_sum,
                    "avg": (total_sum / total_obs) if total_obs > 0 else 0.0,
                }
        return summary

    async def list_trace_records(
        self,
        trace_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        rows, total = await self.repo.list_telemetry(
            trace_id=trace_id, page=page, page_size=page_size
        )
        items = [
            {
                "id": str(row.id),
                "trace_id": row.trace_id,
                "span_id": row.span_id,
                "operation": row.operation,
                "user_id": str(row.user_id) if row.user_id else None,
                "occurred_at": row.occurred_at.isoformat(),
                "duration_ms": row.duration_ms,
                "outcome": row.outcome,
                "detail": row.detail,
            }
            for row in rows
        ]
        return items, total

    async def list_cache_stats(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[CacheHitStatRead], int]:
        rows, total = await self.repo.list_cache_stats(page=page, page_size=page_size)
        return [_cache_stat_to_schema(r) for r in rows], total

    async def list_access_summaries(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        rows, total = await self.repo.list_access_log_summaries(
            from_date=from_date, to_date=to_date, page=page, page_size=page_size
        )
        items = [
            {
                "id": str(r.id),
                "window_start": r.window_start.isoformat(),
                "window_end": r.window_end.isoformat(),
                "endpoint_group": r.endpoint_group,
                "total_requests": r.total_requests,
                "p50_latency_ms": r.p50_latency_ms,
                "p95_latency_ms": r.p95_latency_ms,
                "error_count": r.error_count,
            }
            for r in rows
        ]
        return items, total
