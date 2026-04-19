"""
Pure throttle math. Persistence of LoginThrottle records lives in the auth repo.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def window_contains(window_start: datetime, now: datetime, window_minutes: int) -> bool:
    return now - window_start < timedelta(minutes=window_minutes)


def should_throttle(
    attempt_count: int,
    window_start: datetime,
    now: datetime,
    max_attempts: int,
    window_minutes: int,
) -> bool:
    """True when another attempt must be rejected."""
    if attempt_count < max_attempts:
        return False
    if not window_contains(window_start, now, window_minutes):
        return False
    return True


def is_locked(locked_until: datetime | None, now: datetime) -> bool:
    if locked_until is None:
        return False
    return now < locked_until


def compute_lockout_until(now: datetime, lockout_minutes: int) -> datetime:
    return now + timedelta(minutes=lockout_minutes)


def reset_needed(window_start: datetime, now: datetime, window_minutes: int) -> bool:
    """Window has elapsed — a new attempt starts a fresh window."""
    return not window_contains(window_start, now, window_minutes)


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)
