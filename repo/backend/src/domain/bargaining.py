from datetime import datetime, timedelta, timezone


class BargainingError(Exception):
    pass


class OffersExhaustedError(BargainingError):
    pass


class BargainingWindowClosedError(BargainingError):
    pass


class CounterAlreadyMadeError(BargainingError):
    pass


MAX_OFFERS = 3
WINDOW_HOURS = 48


def can_submit_offer(
    current_offer_count: int,
    window_start: datetime,
    now: datetime,
    max_offers: int = MAX_OFFERS,
    window_hours: int = WINDOW_HOURS,
) -> None:
    """Raise if the candidate cannot submit another offer."""
    if current_offer_count >= max_offers:
        raise OffersExhaustedError(
            f"Maximum of {max_offers} offers already submitted."
        )
    if is_window_expired(window_start, now, window_hours):
        raise BargainingWindowClosedError(
            f"Bargaining window of {window_hours} hours has elapsed."
        )


def can_counter(current_counter_count: int, max_counters: int = 1) -> None:
    """Raise if the reviewer has already issued a counter-offer."""
    if current_counter_count >= max_counters:
        raise CounterAlreadyMadeError(
            "Reviewer has already issued a counter-offer on this thread."
        )


def is_window_expired(
    window_start: datetime,
    now: datetime,
    window_hours: int = WINDOW_HOURS,
) -> bool:
    """Return True if the bargaining window has elapsed."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if window_start.tzinfo is None:
        window_start = window_start.replace(tzinfo=timezone.utc)
    deadline = window_start + timedelta(hours=window_hours)
    return now >= deadline


def window_expires_at(window_start: datetime, window_hours: int = WINDOW_HOURS) -> datetime:
    """Return the UTC datetime when the bargaining window closes."""
    if window_start.tzinfo is None:
        window_start = window_start.replace(tzinfo=timezone.utc)
    return window_start + timedelta(hours=window_hours)
