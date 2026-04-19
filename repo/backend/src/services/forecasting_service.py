"""
Forecasting service: aggregates historical request volume and document-size
data, computes naive trend forecasts, persists ForecastSnapshot rows.

Uses access_log_summaries as the input source (written by the cache_stats
worker from in-process metrics). Forecast method: simple linear extrapolation
of the rolling average over the input window.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..persistence.repositories.config_repo import ConfigRepository
from ..schemas.audit import ForecastSnapshotRead


def _snap_to_schema(snap) -> ForecastSnapshotRead:
    return ForecastSnapshotRead(
        id=snap.id,
        computed_at=snap.computed_at,
        forecast_horizon_days=snap.forecast_horizon_days,
        request_volume_forecast=snap.request_volume_forecast,
        bandwidth_p50_bytes=snap.bandwidth_p50_bytes,
        bandwidth_p95_bytes=snap.bandwidth_p95_bytes,
        upload_volume_trend=snap.upload_volume_trend,
        input_window_days=snap.input_window_days,
    )


class ForecastingService:
    # Average document size assumptions for bandwidth estimation (bytes)
    AVG_DOC_SIZE_P50 = 500_000   # 500 KB (typical PDF)
    AVG_DOC_SIZE_P95 = 5_000_000  # 5 MB (large scan)

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ConfigRepository(session)

    async def compute_forecast(
        self,
        horizon_days: int = 30,
        input_window_days: int = 90,
    ) -> ForecastSnapshotRead:
        now = datetime.now(tz=timezone.utc)
        from_date = now - timedelta(days=input_window_days)
        summaries, _ = await self.repo.list_access_log_summaries(
            from_date=from_date, to_date=now, page=1, page_size=10000
        )

        # Aggregate total_requests per window
        total_requests = sum(s.total_requests for s in summaries)
        n_windows = len(summaries) if summaries else 1
        avg_per_window = total_requests / n_windows

        # Compute daily average (windows are 15-min, so 96 windows/day)
        windows_per_day = 96
        avg_daily = avg_per_window * windows_per_day

        # Simple linear forecast: flat if no trend data, else extrapolate
        request_volume_forecast: dict = {}
        for day in range(1, horizon_days + 1):
            target = now + timedelta(days=day)
            date_str = target.strftime("%Y-%m-%d")
            # Flat projection (extend with trend analysis when more data available)
            request_volume_forecast[date_str] = round(avg_daily)

        # Bandwidth estimate based on request volume and assumed avg doc size
        total_forecast_requests = sum(request_volume_forecast.values())
        # Assume ~5% of requests are document uploads
        estimated_uploads = total_forecast_requests * 0.05
        bandwidth_p50 = int(estimated_uploads * self.AVG_DOC_SIZE_P50) if estimated_uploads > 0 else None
        bandwidth_p95 = int(estimated_uploads * self.AVG_DOC_SIZE_P95) if estimated_uploads > 0 else None

        # Upload volume trend (simple ratio per input window)
        upload_volume_trend = {
            "input_window_days": input_window_days,
            "total_requests_observed": total_requests,
            "avg_daily_requests": round(avg_daily, 2),
            "estimated_daily_uploads": round(estimated_uploads / max(horizon_days, 1), 2),
        }

        snap = await self.repo.create_forecast_snapshot(
            computed_at=now,
            forecast_horizon_days=horizon_days,
            request_volume_forecast=request_volume_forecast,
            bandwidth_p50_bytes=bandwidth_p50,
            bandwidth_p95_bytes=bandwidth_p95,
            upload_volume_trend=upload_volume_trend,
            input_window_days=input_window_days,
            notes=f"Computed from {len(summaries)} access log windows",
        )
        return _snap_to_schema(snap)

    async def list_forecasts(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[ForecastSnapshotRead], int]:
        snaps, total = await self.repo.list_forecast_snapshots(page=page, page_size=page_size)
        return [_snap_to_schema(s) for s in snaps], total

    async def get_latest_forecast(self) -> ForecastSnapshotRead | None:
        snap = await self.repo.get_latest_forecast()
        return _snap_to_schema(snap) if snap else None
