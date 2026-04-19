"""
Nonce freshness and replay defense.

Pure helpers live here. `record_nonce()` persists a row and raises
`NonceReplayError` on the UNIQUE collision surfaced by PostgreSQL.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..persistence.models.auth import Nonce
from .errors import ClockSkewError, NonceReplayError


def parse_iso_timestamp(ts: str) -> datetime:
    """Parse ISO-8601 UTC timestamps tolerantly. Accepts trailing 'Z'."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_clock_skew(client_ts: datetime, now: datetime, tolerance_seconds: int) -> bool:
    delta = abs((now - client_ts).total_seconds())
    return delta > tolerance_seconds


def assert_fresh_timestamp(
    client_ts_str: str,
    now: datetime,
    tolerance_seconds: int,
) -> datetime:
    try:
        client_ts = parse_iso_timestamp(client_ts_str)
    except ValueError as exc:
        raise ClockSkewError("Invalid timestamp format.") from exc
    if is_clock_skew(client_ts, now, tolerance_seconds):
        raise ClockSkewError(
            f"Request timestamp outside ±{tolerance_seconds}s tolerance."
        )
    return client_ts


def compute_nonce_expiry(now: datetime, window_seconds: int) -> datetime:
    return now + timedelta(seconds=window_seconds)


async def record_nonce(
    session: AsyncSession,
    *,
    nonce_value: str,
    expires_at: datetime,
    user_id=None,
    now: datetime | None = None,
) -> None:
    """Insert nonce atomically. UNIQUE violation = replay."""
    row = Nonce(
        nonce_value=nonce_value,
        created_at=now or datetime.now(tz=timezone.utc),
        expires_at=expires_at,
        user_id=user_id,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise NonceReplayError("Nonce has already been used.") from exc
