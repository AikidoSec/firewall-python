import pytest
import time
from .rate_limiter import RateLimiter


@pytest.fixture
def rate_limiter():
    max_items = 10
    time_to_live_in_ms = 1000  # 1 second TTL
    return RateLimiter(max_items, time_to_live_in_ms)


def test_allow_requests_within_limit(rate_limiter):
    key = "user1"
    for i in range(5):
        assert rate_limiter.is_allowed(
            key, 5000000, 5
        ), f"Request {i + 1} should be allowed"


def test_deny_requests_exceeding_limit(rate_limiter):
    key = "user2"
    for i in range(5):
        rate_limiter.is_allowed(key, 500, 5)
    assert not rate_limiter.is_allowed(key, 500, 5), "Request 6 should not be allowed"


def test_clear_old_entries(rate_limiter):
    key = "user3"
    for i in range(5):
        rate_limiter.is_allowed(key, 500, 5)

    time.sleep(0.6)  # Sleep to allow old entries to be cleared

    assert rate_limiter.is_allowed(
        key, 500, 5
    ), "New request should be allowed after clearing old entries"


def test_multiple_keys(rate_limiter):
    key1 = "user4"
    key2 = "user5"

    for i in range(5):
        assert rate_limiter.is_allowed(
            key1, 500, 5
        ), f"Request {i + 1} for key1 should be allowed"
    for i in range(5):
        assert rate_limiter.is_allowed(
            key2, 500, 5
        ), f"Request {i + 1} for key2 should be allowed"

    assert not rate_limiter.is_allowed(
        key1, 500, 5
    ), "Request 6 for key1 should not be allowed"
    assert not rate_limiter.is_allowed(
        key2, 500, 5
    ), "Request 6 for key2 should not be allowed"


def test_ttl_expiration(rate_limiter):
    key = "user6"
    for i in range(5):
        rate_limiter.is_allowed(key, 500, 5)

    time.sleep(1.1)  # Sleep to allow the TTL to expire

    assert rate_limiter.is_allowed(key, 500, 5), "Request after TTL should be allowed"


def test_allow_requests_exactly_at_limit(rate_limiter):
    key = "user7"
    for i in range(5):
        assert rate_limiter.is_allowed(
            key, 500, 5
        ), f"Request {i + 1} should be allowed"
    assert not rate_limiter.is_allowed(key, 500, 5), "Request 6 should not be allowed"


def test_allow_requests_after_clearing_old_entries(rate_limiter):
    key = "user8"
    for i in range(5):
        rate_limiter.is_allowed(key, 500, 5)

    time.sleep(0.6)  # Sleep to allow old entries to be cleared

    assert rate_limiter.is_allowed(
        key, 500, 5
    ), "New request should be allowed after clearing old entries"


def test_multiple_rapid_requests(rate_limiter):
    key = "user9"
    for i in range(5):
        assert rate_limiter.is_allowed(
            key, 500, 5
        ), f"Request {i + 1} should be allowed"

    time.sleep(0.1)  # Sleep for 100 ms

    assert not rate_limiter.is_allowed(
        key, 500, 5
    ), "Request after rapid requests should not be allowed"


def test_reset_after_ttl(rate_limiter):
    key = "user10"
    for i in range(5):
        rate_limiter.is_allowed(key, 500, 5)

    time.sleep(1.1)  # Sleep to allow the TTL to expire

    assert rate_limiter.is_allowed(key, 500, 5), "Request after TTL should be allowed"


def test_different_window_sizes(rate_limiter):
    key = "user11"
    different_window_size = 1000  # 1 second window
    for i in range(5):
        assert rate_limiter.is_allowed(
            key, different_window_size, 5
        ), f"Request {i + 1} should be allowed"
    assert not rate_limiter.is_allowed(
        key, different_window_size, 5
    ), "Request 6 should not be allowed"


def test_sliding_window_with_intermittent_requests(rate_limiter):
    key = "user14"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.is_allowed(
            key, 500, 5
        ), f"Request {i + 1} should be allowed"
        time.sleep(0.1)  # Sleep 100 ms between requests

    # Sleep for 600 ms to allow the first requests to slide out of the window
    time.sleep(0.6)

    # Now we should be able to make a new request
    assert rate_limiter.is_allowed(
        key, 500, 5
    ), "New request should be allowed after sliding"


def test_sliding_window_edge_case(rate_limiter):
    key = "user15"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.is_allowed(
            key, 500, 5
        ), f"Request {i + 1} should be allowed"

    # Sleep for 500 ms to simulate time passing
    time.sleep(0.6)

    # The next request should still be allowed as the window is sliding
    assert rate_limiter.is_allowed(
        key, 500, 5
    ), "Next request should be allowed as window slides"

    # Sleep for another 500 ms to allow the first batch to expire
    time.sleep(0.6)

    # Now we should be able to make a new request
    assert rate_limiter.is_allowed(
        key, 500, 5
    ), "New request should be allowed after first batch expires"


def test_sliding_window_with_burst_requests(rate_limiter):
    key = "user16"
    window_size_ms = 500

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.is_allowed(
            key, window_size_ms, 5
        ), f"Request {i + 1} should be allowed"

    # Sleep for 250 ms to simulate time passing
    time.sleep((window_size_ms / 2) / 1000)

    # Add 3 more requests (should be denied)
    assert not rate_limiter.is_allowed(
        key, window_size_ms, 5
    ), "Request should not be allowed"
    assert not rate_limiter.is_allowed(
        key, window_size_ms, 5
    ), "Request should not be allowed"
    assert not rate_limiter.is_allowed(
        key, window_size_ms, 5
    ), "Request should not be allowed"

    time.sleep(
        (window_size_ms / 2 + 50) / 1000
    )  # 50ms buffer, first requests are still in window

    # Make a burst of requests (should be allowed)
    for i in range(2):
        assert rate_limiter.is_allowed(
            key, window_size_ms, 5
        ), f"Burst request {i + 1} should be allowed"
    assert not rate_limiter.is_allowed(
        key, window_size_ms, 5
    ), "Burst request should not be allowed after limit"

    # Sleep for 500 ms to allow all batches to slide out of window
    time.sleep((window_size_ms + 100) / 1000)

    # Now we should be able to make a new request
    assert rate_limiter.is_allowed(
        key, window_size_ms, 5
    ), "New request should be allowed after all batches slide out"


def test_sliding_window_with_delayed_requests(rate_limiter):
    key = "user17"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.is_allowed(
            key, 500, 5
        ), f"Request {i + 1} should be allowed"
        time.sleep(0.1)  # Sleep 100 ms between requests

    # Sleep for 600 ms to allow the first requests to slide out of the window
    time.sleep(0.6)

    # Now we should be able to make a new request
    assert rate_limiter.is_allowed(
        key, 500, 5
    ), "New request should be allowed after sliding"
