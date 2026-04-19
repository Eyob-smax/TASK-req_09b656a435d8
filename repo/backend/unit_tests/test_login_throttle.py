"""
Login throttle pure math (persistence tested in API integration tests).
"""
from datetime import datetime, timedelta, timezone

from src.security.throttling import (
    compute_lockout_until,
    is_locked,
    reset_needed,
    should_throttle,
    window_contains,
)


def _at(offset_min: float) -> datetime:
    base = datetime(2026, 4, 18, tzinfo=timezone.utc)
    return base + timedelta(minutes=offset_min)


def test_window_contains_true_within_window():
    assert window_contains(_at(0), _at(5), 15) is True


def test_window_contains_false_outside_window():
    assert window_contains(_at(0), _at(20), 15) is False


def test_should_throttle_below_threshold_returns_false():
    assert should_throttle(3, _at(0), _at(5), max_attempts=5, window_minutes=15) is False


def test_should_throttle_at_threshold_returns_true():
    assert should_throttle(5, _at(0), _at(5), max_attempts=5, window_minutes=15) is True


def test_should_throttle_outside_window_returns_false():
    assert should_throttle(10, _at(0), _at(30), max_attempts=5, window_minutes=15) is False


def test_is_locked_no_lockout():
    assert is_locked(None, _at(0)) is False


def test_is_locked_future_locked():
    assert is_locked(_at(30), _at(0)) is True


def test_is_locked_past_unlocked():
    assert is_locked(_at(0), _at(30)) is False


def test_compute_lockout_until_adds_minutes():
    now = _at(0)
    until = compute_lockout_until(now, 15)
    assert until - now == timedelta(minutes=15)


def test_reset_needed_after_window():
    assert reset_needed(_at(0), _at(20), 15) is True


def test_reset_not_needed_within_window():
    assert reset_needed(_at(0), _at(5), 15) is False
