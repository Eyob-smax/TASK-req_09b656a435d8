"""
Lightweight trace/span correlation.

`new_trace_id()` generates opaque 128-bit IDs. `bind_trace(trace_id)` binds
the trace ID into structlog's contextvars. `span(...)` is an async context
manager that, when a `session` is supplied, writes a row into
`telemetry_correlations` capturing operation, duration, and outcome.
"""
from __future__ import annotations

import contextlib
import secrets
import time
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..persistence.models.config_audit import TelemetryCorrelation


def new_trace_id() -> str:
    return secrets.token_hex(16)


def new_span_id() -> str:
    return secrets.token_hex(8)


def bind_trace(trace_id: str) -> None:
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def clear_trace() -> None:
    structlog.contextvars.clear_contextvars()


@contextlib.asynccontextmanager
async def span(
    operation: str,
    *,
    session: AsyncSession | None = None,
    user_id: uuid.UUID | None = None,
    trace_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """
    Async span context manager.

    Usage:
        async with span("auth.login", session=session, user_id=user.id) as ctx:
            ctx["detail"]["idp_client_id"] = client_id
    """
    trace = trace_id or new_trace_id()
    span_id = new_span_id()
    started = time.perf_counter()
    start_dt = datetime.now(tz=timezone.utc)
    ctx: dict[str, Any] = {
        "trace_id": trace,
        "span_id": span_id,
        "operation": operation,
        "detail": dict(detail or {}),
        "outcome": "success",
    }
    bind_trace(trace)
    try:
        yield ctx
    except Exception as exc:
        ctx["outcome"] = "error"
        ctx["detail"]["error_type"] = type(exc).__name__
        raise
    finally:
        duration_ms = int((time.perf_counter() - started) * 1000)
        if session is not None:
            row = TelemetryCorrelation(
                trace_id=trace,
                span_id=span_id,
                operation=operation,
                user_id=user_id,
                occurred_at=start_dt,
                duration_ms=duration_ms,
                outcome=ctx["outcome"],
                detail=ctx["detail"] or None,
            )
            session.add(row)


async def record_correlation(
    session: AsyncSession,
    *,
    trace_id: str,
    operation: str,
    outcome: str,
    user_id: uuid.UUID | None = None,
    duration_ms: int | None = None,
    detail: dict[str, Any] | None = None,
    span_id: str | None = None,
) -> TelemetryCorrelation:
    row = TelemetryCorrelation(
        trace_id=trace_id,
        span_id=span_id,
        operation=operation,
        user_id=user_id,
        occurred_at=datetime.now(tz=timezone.utc),
        duration_ms=duration_ms,
        outcome=outcome,
        detail=detail,
    )
    session.add(row)
    await session.flush()
    return row
