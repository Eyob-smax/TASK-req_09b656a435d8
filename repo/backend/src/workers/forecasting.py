"""
Background worker: periodic forecast computation.

Runs every 3600 seconds (1 hour). Computes a 30-day forecast from the last
90 days of access log summaries and persists a ForecastSnapshot. Errors per
iteration are caught and logged; the loop does not crash on single failures.
"""
from __future__ import annotations

import asyncio

import structlog

from ..services.forecasting_service import ForecastingService

logger = structlog.get_logger("workers.forecasting")


async def run_forecasting_loop(
    session_factory,
    interval_seconds: int = 3600,
    horizon_days: int = 30,
    input_window_days: int = 90,
) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        async with session_factory() as session:
            try:
                svc = ForecastingService(session)
                snap = await svc.compute_forecast(
                    horizon_days=horizon_days,
                    input_window_days=input_window_days,
                )
                await session.commit()
                logger.info(
                    "forecast_computed",
                    snapshot_id=str(snap.id),
                    horizon_days=horizon_days,
                )
            except Exception:
                await session.rollback()
                logger.exception("forecasting_loop_error")
