from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from ..domain.enums import OrderStatus
from ..persistence.models.order import RefundRecord, Order
from ..persistence.repositories.auth_repo import now_utc
from ..telemetry.logging import get_logger
from ..telemetry.metrics import registry

logger = get_logger("workers.refund_progression")

STALE_REFUND_DAYS = 7
_stale_refund_metric = registry.counter("merittrack_stale_refunds_total", "Refunds stale > 7 days")


async def run_refund_progression_loop(
    session_factory, interval_seconds: int = 3600
) -> None:
    """
    Refund processing is a manual admin action. This worker monitors for
    refunds that have been in-progress for more than 7 days and logs a metric.
    No automatic progression occurs.
    """
    while True:
        await asyncio.sleep(interval_seconds)
        async with session_factory() as session:
            try:
                now = now_utc()
                cutoff = now - timedelta(days=STALE_REFUND_DAYS)
                q = (
                    select(RefundRecord)
                    .join(Order, Order.id == RefundRecord.order_id)
                    .where(
                        Order.status == OrderStatus.refund_in_progress.value,
                        RefundRecord.initiated_at <= cutoff,
                        RefundRecord.processed_by.is_(None),
                    )
                )
                stale = list((await session.execute(q)).scalars().all())
                if stale:
                    _stale_refund_metric.inc(len(stale))
                    logger.warning(
                        "stale_refunds_detected",
                        count=len(stale),
                        order_ids=[str(r.order_id) for r in stale],
                    )
            except Exception:
                logger.exception("refund_progression_loop_error")
