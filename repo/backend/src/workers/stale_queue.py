from __future__ import annotations

import asyncio

from sqlalchemy import delete

from ..persistence.models.auth import Nonce
from ..persistence.models.idempotency import IdempotencyKey
from ..persistence.repositories.auth_repo import now_utc
from ..telemetry.logging import get_logger

logger = get_logger("workers.stale_queue")


async def run_stale_queue_loop(
    session_factory, interval_seconds: int = 600
) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        async with session_factory() as session:
            try:
                now = now_utc()
                nonce_result = await session.execute(
                    delete(Nonce).where(Nonce.expires_at < now)
                )
                idem_result = await session.execute(
                    delete(IdempotencyKey).where(IdempotencyKey.expires_at < now)
                )
                await session.commit()
                logger.info(
                    "stale_queue_cleanup",
                    nonces_deleted=nonce_result.rowcount,
                    idempotency_keys_deleted=idem_result.rowcount,
                )
            except Exception:
                await session.rollback()
                logger.exception("stale_queue_loop_error")
