from datetime import datetime, timedelta, timezone

import pytest

from src.domain.bargaining import (
    BargainingWindowClosedError,
    CounterAlreadyMadeError,
    OffersExhaustedError,
    can_counter,
    can_submit_offer,
    window_expires_at,
    is_window_expired,
)


NOW = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
WINDOW_START = NOW - timedelta(hours=10)
EXPIRED_WINDOW_START = NOW - timedelta(hours=49)


class TestCanSubmitOffer:
    def test_first_offer_allowed(self):
        can_submit_offer(0, WINDOW_START, NOW)

    def test_second_offer_allowed(self):
        can_submit_offer(1, WINDOW_START, NOW)

    def test_third_offer_allowed(self):
        can_submit_offer(2, WINDOW_START, NOW)

    def test_fourth_offer_blocked(self):
        with pytest.raises(OffersExhaustedError):
            can_submit_offer(3, WINDOW_START, NOW)

    def test_offer_after_window_expiry_blocked(self):
        with pytest.raises(BargainingWindowClosedError):
            can_submit_offer(0, EXPIRED_WINDOW_START, NOW)

    def test_offer_at_exact_48h_boundary_blocked(self):
        exactly_expired = NOW - timedelta(hours=48)
        with pytest.raises(BargainingWindowClosedError):
            can_submit_offer(0, exactly_expired, NOW)

    def test_offer_just_before_48h_allowed(self):
        just_before = NOW - timedelta(hours=47, minutes=59)
        can_submit_offer(0, just_before, NOW)


class TestCanCounter:
    def test_counter_allowed_when_count_zero(self):
        can_counter(0)

    def test_counter_blocked_when_count_one(self):
        with pytest.raises(CounterAlreadyMadeError):
            can_counter(1)

    def test_counter_blocked_when_count_two(self):
        with pytest.raises(CounterAlreadyMadeError):
            can_counter(2)


class TestWindowExpiry:
    def test_window_not_expired_within_48h(self):
        assert is_window_expired(WINDOW_START, NOW) is False

    def test_window_expired_after_48h(self):
        assert is_window_expired(EXPIRED_WINDOW_START, NOW) is True

    def test_expiry_datetime_is_48h_after_start(self):
        expiry = window_expires_at(WINDOW_START)
        expected = WINDOW_START + timedelta(hours=48)
        assert expiry == expected

    def test_naive_datetime_treated_as_utc(self):
        naive_start = datetime(2025, 5, 30, 0, 0, 0)
        naive_now = datetime(2025, 6, 1, 1, 0, 0)
        assert is_window_expired(naive_start, naive_now) is True
