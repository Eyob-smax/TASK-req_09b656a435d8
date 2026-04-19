from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from ..domain.enums import UserRole
from ..persistence.repositories.auth_repo import now_utc
from ..persistence.repositories.order_repo import OrderRepository
from ..security.rbac import Actor
from ..services.order_service import OrderService
from ..telemetry.logging import get_logger

logger = get_logger("workers.auto_cancel")

SYSTEM_ACTOR = Actor(
    user_id="00000000-0000-0000-0000-000000000000",
    role=UserRole.admin,
    username="system",
)


async def run_auto_cancel_loop(session_factory, interval_seconds: int = 60) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        async with session_factory() as session:
            try:
                now = now_utc()
                repo = OrderRepository(session)
                svc = OrderService(session)
                overdue = await repo.pending_payment_overdue(now)
                for order in overdue:
                    try:
                        await svc.cancel(order.id, SYSTEM_ACTOR, "auto_cancel_inactivity")
                    except Exception:
                        logger.exception("auto_cancel_order_error", order_id=str(order.id))
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("auto_cancel_loop_error")
