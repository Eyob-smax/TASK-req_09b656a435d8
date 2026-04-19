"""
Nonce / clock-skew primitives (pure).
"""
from datetime import datetime, timedelta, timezone

import pytest

from src.security.errors import ClockSkewError
from src.security.nonce import (
    assert_fresh_timestamp,
    compute_nonce_expiry,
    is_clock_skew,
    parse_iso_timestamp,
)


def _now() -> datetime:
    return datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_iso_trailing_z():
    dt = parse_iso_timestamp("2026-04-18T12:00:00Z")
    assert dt.tzinfo is not None
    assert dt == datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_iso_offset():
    dt = parse_iso_timestamp("2026-04-18T17:30:00+05:30")
    assert dt.astimezone(timezone.utc) == datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc)


def test_clock_skew_within_tolerance():
    now = _now()
    close = now + timedelta(seconds=10)
    assert is_clock_skew(close, now, 30) is False


def test_clock_skew_outside_tolerance():
    now = _now()
    far = now + timedelta(seconds=60)
    assert is_clock_skew(far, now, 30) is True


def test_assert_fresh_timestamp_happy():
    ts = "2026-04-18T12:00:15Z"
    assert_fresh_timestamp(ts, _now(), tolerance_seconds=30)


def test_assert_fresh_timestamp_invalid():
    with pytest.raises(ClockSkewError):
        assert_fresh_timestamp("not-a-timestamp", _now(), tolerance_seconds=30)


def test_assert_fresh_timestamp_too_old():
    ts = "2026-04-18T11:00:00Z"
    with pytest.raises(ClockSkewError):
        assert_fresh_timestamp(ts, _now(), tolerance_seconds=30)


def test_compute_nonce_expiry_in_future():
    now = _now()
    assert compute_nonce_expiry(now, 300) == now + timedelta(minutes=5)
