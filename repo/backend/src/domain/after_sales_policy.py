from datetime import datetime, timedelta, timezone


class AfterSalesWindowExpiredError(Exception):
    pass


DEFAULT_WINDOW_DAYS = 14


def _ensure_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def compute_window_expiry(
    completed_at: datetime,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> datetime:
    """Return the UTC datetime after which no after-sales requests are accepted."""
    return _ensure_tz(completed_at) + timedelta(days=window_days)


def is_within_window(
    completed_at: datetime,
    now: datetime,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> bool:
    """Return True if the current time is within the after-sales eligibility window."""
    expiry = compute_window_expiry(completed_at, window_days)
    return _ensure_tz(now) <= expiry


def assert_within_window(
    completed_at: datetime,
    now: datetime,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> None:
    """Raise AfterSalesWindowExpiredError if the window has passed."""
    if not is_within_window(completed_at, now, window_days):
        expiry = compute_window_expiry(completed_at, window_days)
        raise AfterSalesWindowExpiredError(
            f"After-sales requests are only accepted within {window_days} days of completion. "
            f"Window closed at {expiry.isoformat()}."
        )
