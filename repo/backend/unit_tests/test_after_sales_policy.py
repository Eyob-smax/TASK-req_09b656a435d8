from datetime import datetime, timedelta, timezone

import pytest

from src.domain.after_sales_policy import (
    AfterSalesWindowExpiredError,
    assert_within_window,
    compute_window_expiry,
    is_within_window,
)


COMPLETED_AT = datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
WINDOW_DAYS = 14


class TestIsWithinWindow:
    def test_request_one_day_after_completion_allowed(self):
        now = COMPLETED_AT + timedelta(days=1)
        assert is_within_window(COMPLETED_AT, now, WINDOW_DAYS) is True

    def test_request_exactly_on_day_14_allowed(self):
        now = COMPLETED_AT + timedelta(days=14)
        assert is_within_window(COMPLETED_AT, now, WINDOW_DAYS) is True

    def test_request_on_day_15_blocked(self):
        now = COMPLETED_AT + timedelta(days=15)
        assert is_within_window(COMPLETED_AT, now, WINDOW_DAYS) is False

    def test_request_one_second_past_expiry_blocked(self):
        now = COMPLETED_AT + timedelta(days=14, seconds=1)
        assert is_within_window(COMPLETED_AT, now, WINDOW_DAYS) is False

    def test_request_one_second_before_expiry_allowed(self):
        now = COMPLETED_AT + timedelta(days=14) - timedelta(seconds=1)
        assert is_within_window(COMPLETED_AT, now, WINDOW_DAYS) is True

    def test_naive_datetime_treated_as_utc(self):
        naive_completed = datetime(2025, 5, 1, 12, 0, 0)
        naive_now = datetime(2025, 5, 5, 12, 0, 0)
        assert is_within_window(naive_completed, naive_now, WINDOW_DAYS) is True


class TestComputeWindowExpiry:
    def test_expiry_is_14_days_after_completion(self):
        expiry = compute_window_expiry(COMPLETED_AT, WINDOW_DAYS)
        expected = COMPLETED_AT + timedelta(days=14)
        assert expiry == expected

    def test_custom_window_days(self):
        expiry = compute_window_expiry(COMPLETED_AT, window_days=30)
        expected = COMPLETED_AT + timedelta(days=30)
        assert expiry == expected


class TestAssertWithinWindow:
    def test_within_window_does_not_raise(self):
        now = COMPLETED_AT + timedelta(days=5)
        assert_within_window(COMPLETED_AT, now, WINDOW_DAYS)

    def test_past_window_raises(self):
        now = COMPLETED_AT + timedelta(days=15)
        with pytest.raises(AfterSalesWindowExpiredError):
            assert_within_window(COMPLETED_AT, now, WINDOW_DAYS)
