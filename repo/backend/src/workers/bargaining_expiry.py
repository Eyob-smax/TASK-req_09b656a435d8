from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from ..persistence.repositories.auth_repo import now_utc
from ..persistence.repositories.order_repo import OrderRepository
from ..services.bargaining_service import BargainingService
from ..telemetry.logging import get_logger

logger = get_logger("workers.bargaining_expiry")


async def run_bargaining_expiry_loop(
    session_factory, interval_seconds: int = 60
) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        async with session_factory() as session:
            try:
                now = now_utc()
                repo = OrderRepository(session)
                svc = BargainingService(session)
                expired_threads = await repo.open_bargaining_threads_expired(now)
                for thread in expired_threads:
                    try:
                        await svc.expire_thread(thread, now)
                    except Exception:
                        logger.exception(
                            "bargaining_expiry_thread_error",
                            thread_id=str(thread.id),
                        )
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("bargaining_expiry_loop_error")
