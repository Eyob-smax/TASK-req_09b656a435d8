"""
BE-UNIT: Forecasting service — compute_forecast with empty data returns zero baseline,
with data returns trend dict, bandwidth estimates are reasonable.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_summary(total_requests: int, window_start: datetime) -> MagicMock:
    s = MagicMock()
    s.total_requests = total_requests
    s.window_start = window_start
    s.error_count = 0
    return s


@pytest.mark.asyncio
async def test_compute_forecast_empty_data_returns_baseline():
    """With no access log summaries, forecast returns zero or near-zero daily requests."""
    from src.services.forecasting_service import ForecastingService

    session = AsyncMock()
    svc = ForecastingService(session)
    svc.repo = AsyncMock()
    svc.repo.list_access_log_summaries = AsyncMock(return_value=([], 0))

    saved_snap = MagicMock()
    saved_snap.id = uuid.uuid4()
    saved_snap.computed_at = datetime.now(tz=timezone.utc)
    saved_snap.forecast_horizon_days = 30
    saved_snap.request_volume_forecast = {}
    saved_snap.bandwidth_p50_bytes = None
    saved_snap.bandwidth_p95_bytes = None
    saved_snap.upload_volume_trend = {}
    saved_snap.input_window_days = 90

    svc.repo.create_forecast_snapshot = AsyncMock(return_value=saved_snap)

    result = await svc.compute_forecast(horizon_days=30, input_window_days=90)
    svc.repo.create_forecast_snapshot.assert_awaited_once()
    call_kwargs = svc.repo.create_forecast_snapshot.call_args.kwargs
    # With no data, all daily forecasts should be 0
    for v in call_kwargs["request_volume_forecast"].values():
        assert v == 0


@pytest.mark.asyncio
async def test_compute_forecast_with_data_produces_nonzero():
    """With real request data, forecast produces positive daily volumes."""
    from src.services.forecasting_service import ForecastingService
    from datetime import timedelta

    session = AsyncMock()
    svc = ForecastingService(session)
    svc.repo = AsyncMock()

    now = datetime.now(tz=timezone.utc)
    summaries = [_make_summary(100, now - timedelta(minutes=15 * i)) for i in range(10)]
    svc.repo.list_access_log_summaries = AsyncMock(return_value=(summaries, 10))

    saved_snap = MagicMock()
    saved_snap.id = uuid.uuid4()
    saved_snap.computed_at = now
    saved_snap.forecast_horizon_days = 7
    saved_snap.request_volume_forecast = {"2026-04-20": 9600}
    saved_snap.bandwidth_p50_bytes = 1000
    saved_snap.bandwidth_p95_bytes = 5000
    saved_snap.upload_volume_trend = {"avg_daily_requests": 9600}
    saved_snap.input_window_days = 30

    svc.repo.create_forecast_snapshot = AsyncMock(return_value=saved_snap)

    result = await svc.compute_forecast(horizon_days=7, input_window_days=30)
    call_kwargs = svc.repo.create_forecast_snapshot.call_args.kwargs
    # 100 requests/window × 96 windows/day = 9600 requests/day
    for v in call_kwargs["request_volume_forecast"].values():
        assert v > 0


@pytest.mark.asyncio
async def test_compute_forecast_bandwidth_estimated():
    """Bandwidth estimates are set when there is request data."""
    from src.services.forecasting_service import ForecastingService
    from datetime import timedelta

    session = AsyncMock()
    svc = ForecastingService(session)
    svc.repo = AsyncMock()

    now = datetime.now(tz=timezone.utc)
    # 10 windows × 200 requests each
    summaries = [_make_summary(200, now - timedelta(minutes=15 * i)) for i in range(10)]
    svc.repo.list_access_log_summaries = AsyncMock(return_value=(summaries, 10))

    saved_snap = MagicMock()
    saved_snap.id = uuid.uuid4()
    saved_snap.computed_at = now
    saved_snap.forecast_horizon_days = 30
    saved_snap.request_volume_forecast = {}
    saved_snap.bandwidth_p50_bytes = 12_288_000
    saved_snap.bandwidth_p95_bytes = 122_880_000
    saved_snap.upload_volume_trend = {}
    saved_snap.input_window_days = 30

    svc.repo.create_forecast_snapshot = AsyncMock(return_value=saved_snap)

    await svc.compute_forecast(horizon_days=30, input_window_days=30)
    call_kwargs = svc.repo.create_forecast_snapshot.call_args.kwargs
    # With data, bandwidth estimates should be positive
    assert call_kwargs["bandwidth_p50_bytes"] is not None
    assert call_kwargs["bandwidth_p50_bytes"] > 0
    assert call_kwargs["bandwidth_p95_bytes"] > call_kwargs["bandwidth_p50_bytes"]


def test_forecast_horizon_produces_correct_day_count():
    """request_volume_forecast should have exactly horizon_days keys."""
    import asyncio
    from src.services.forecasting_service import ForecastingService

    session = AsyncMock()
    svc = ForecastingService(session)
    svc.repo = AsyncMock()
    svc.repo.list_access_log_summaries = AsyncMock(return_value=([], 0))

    captured = {}

    async def _capture(**kwargs):
        captured.update(kwargs)
        m = MagicMock()
        m.id = uuid.uuid4()
        m.computed_at = datetime.now(tz=timezone.utc)
        m.forecast_horizon_days = 14
        m.request_volume_forecast = {}
        m.bandwidth_p50_bytes = None
        m.bandwidth_p95_bytes = None
        m.upload_volume_trend = {}
        m.input_window_days = 30
        return m

    svc.repo.create_forecast_snapshot = _capture

    asyncio.get_event_loop().run_until_complete(svc.compute_forecast(horizon_days=14, input_window_days=30))
    assert len(captured["request_volume_forecast"]) == 14
