import pytest
import time

from .fixed_window_rate_limiter import FixedWindowRateLimiter
from .rate_limiter import RateLimiter
from .sliding_window_rate_limiter import SlidingWindowRateLimiter


# Assuming the RateLimiter class is defined above
window_size = 500
max_requests = 5


@pytest.fixture
def rate_limiter():
    max_amount = 5
    ttl = 1000  # 0.5 seconds
    return SlidingWindowRateLimiter(max_amount, ttl)


def test_allow_up_to_max_amount_requests_within_ttl(rate_limiter):
    key = "user1"
    for i in range(rate_limiter.max_items):
        assert rate_limiter.is_allowed(
            key, window_size, max_requests
        ), f"Request {i + 1} should be allowed"

    assert not rate_limiter.is_allowed(
        key, window_size, max_requests
    ), "Request 6 should not be allowed"


def test_reset_after_ttl_expired(rate_limiter):
    key = "user1"
    for i in range(rate_limiter.max_items):
        assert rate_limiter.is_allowed(
            key, window_size, max_requests
        ), f"Request {i + 1} should be allowed"

    assert not rate_limiter.is_allowed(
        key, window_size, max_requests
    ), "Request 6 should not be allowed"

    # Simulate the passage of time
    time.sleep(
        (window_size / 1000) + 0.1
    )  # Convert ms to seconds and add a small buffer

    assert rate_limiter.is_allowed(
        key, window_size, max_requests
    ), "Request after TTL should be allowed"


def test_allow_requests_for_different_keys_independently(rate_limiter):
    key1 = "user1"
    key2 = "user2"

    for i in range(rate_limiter.max_items):
        assert rate_limiter.is_allowed(
            key1, window_size, max_requests
        ), f"Request {i + 1} for key1 should be allowed"

    assert not rate_limiter.is_allowed(
        key1, window_size, max_requests
    ), "Request 6 for key1 should not be allowed"

    for i in range(rate_limiter.max_items):
        assert rate_limiter.is_allowed(
            key2, window_size, max_requests
        ), f"Request {i + 1} for key2 should be allowed"

    assert not rate_limiter.is_allowed(
        key2, window_size, max_requests
    ), "Request 6 for key2 should not be allowed"


def test_allow_requests_within_limit(rate_limiter):
    key = "user1"
    for i in range(5):
        assert rate_limiter.is_allowed(key, 5000000, max_requests)


def test_deny_requests_exceeding_limit(rate_limiter):
    key = "user2"
    for i in range(5):
        rate_limiter.is_allowed(key, window_size, max_requests)
    # The 6th request should be denied
    assert not rate_limiter.is_allowed(key, window_size, max_requests)


def test_clear_old_entries(rate_limiter):
    key = "user3"
    for i in range(5):
        rate_limiter.is_allowed(key, window_size, max_requests)

    # Sleep to allow old entries to be cleared
    time.sleep((window_size / 1000) + 0.1)  # Add a small buffer

    # After sleeping, we should be able to make a new request
    assert rate_limiter.is_allowed(key, window_size, max_requests)


def test_multiple_keys(rate_limiter):
    key1 = "user4"
    key2 = "user5"

    # Allow requests for key1
    for i in range(5):
        assert rate_limiter.is_allowed(key1, window_size, max_requests)

    # Allow requests for key2
    for i in range(5):
        assert rate_limiter.is_allowed(key2, window_size, max_requests)

    # Deny request for key1 after limit
    assert not rate_limiter.is_allowed(key1, window_size, max_requests)
    # Deny request for key2 after limit
    assert not rate_limiter.is_allowed(key2, window_size, max_requests)


def test_ttl_expiration(rate_limiter):
    key = "user6"
    for i in range(5):
        rate_limiter.is_allowed(key, window_size, max_requests)

    # Sleep to allow the TTL to expire
    time.sleep((window_size / 1000) + 0.1)  # Add a small buffer

    # After TTL expiration, we should be able to make a new request
    assert rate_limiter.is_allowed(key, window_size, max_requests)


def test_allow_requests_exactly_at_limit(rate_limiter):
    key = "user7"
    for i in range(5):
        assert rate_limiter.is_allowed(key, window_size, max_requests)
    # The next request should be denied as it hits the limit
    assert not rate_limiter.is_allowed(key, window_size, max_requests)


def test_allow_requests_after_clearing_old_entries(rate_limiter):
    key = "user8"
    for i in range(5):
        rate_limiter.is_allowed(key, window_size, max_requests)

    # Sleep to allow old entries to be cleared
    time.sleep((window_size / 1000) + 0.1)  # Add a small buffer

    # After clearing, we should be able to make a new request
    assert rate_limiter.is_allowed(key, window_size, max_requests)


def test_multiple_rapid_requests(rate_limiter):
    key = "user9"
    for i in range(5):
        assert rate_limiter.is_allowed(key, window_size, max_requests)

    # Sleep for a short time to simulate rapid requests
    time.sleep(0.1)  # Sleep for 100 ms

    # The next request should be denied as it exceeds the limit
    assert not rate_limiter.is_allowed(key, window_size, max_requests)


def test_reset_after_ttl(rate_limiter):
    key = "user10"
    for i in range(5):
        rate_limiter.is_allowed(key, window_size, max_requests)

    # Sleep to allow the TTL to expire
    time.sleep((window_size / 1000) + 0.1)  # Add a small buffer

    # After TTL expiration, we should be able to make a new request
    assert rate_limiter.is_allowed(key, window_size, max_requests)


def test_different_window_sizes(rate_limiter):
    key = "user11"
    different_window_size = 1000  # 1 second window
    for i in range(5):
        assert rate_limiter.is_allowed(key, different_window_size, max_requests)
    # The 6th request should be denied
    assert not rate_limiter.is_allowed(key, different_window_size, max_requests)


def test_sliding_window_with_intermittent_requests(rate_limiter):
    key = "user14"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.is_allowed(key, window_size, max_requests)
        time.sleep(0.1)  # Sleep 100 ms between requests

    # Sleep for 600 ms to allow the first requests to slide out of the window
    time.sleep(0.6)

    # Now we should be able to make a new request
    assert rate_limiter.is_allowed(key, window_size, max_requests)


def test_sliding_window_edge_case(rate_limiter):
    key = "user15"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.is_allowed(key, window_size, max_requests)

    # Sleep for 500 ms to simulate time passing
    time.sleep((window_size / 1000) + 0.1)

    # The next request should still be allowed as the window is sliding
    assert rate_limiter.is_allowed(key, window_size, max_requests)

    # Sleep for another 500 ms to allow the first batch to expire
    time.sleep((window_size / 1000) + 0.1)

    # Now we should be able to make a new request
    assert rate_limiter.is_allowed(key, window_size, max_requests)


def test_sliding_window_with_delayed_requests(rate_limiter):
    key = "user17"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.is_allowed(key, window_size, max_requests)
        time.sleep(0.1)  # Sleep 100 ms between requests

    # Sleep for 600 ms to allow the first requests to slide out of the window
    time.sleep(0.6)

    # Now we should be able to make a new request
    assert rate_limiter.is_allowed(key, window_size, max_requests)


def test_sliding_window_with_burst_requests(rate_limiter):
    key = "user16"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.is_allowed(key, window_size, max_requests)

    # Sleep for 200 ms to simulate time passing
    time.sleep((window_size / 2) / 1000)  # Sleep for 250 ms

    # Attempt to add 3 more requests (should be denied)
    assert not rate_limiter.is_allowed(key, window_size, max_requests)
    assert not rate_limiter.is_allowed(key, window_size, max_requests)
    assert not rate_limiter.is_allowed(key, window_size, max_requests)
    # Sleep for a bit longer to allow the first requests to slide out of the window
    time.sleep(
        (window_size / 2 + 50) / 1000
    )  # Sleep for 600 ms to ensure the first batch is out of the window

    # Make a burst of requests (should be allowed)
    for i in range(2):
        assert rate_limiter.is_allowed(key, window_size, max_requests)

    # The next request should be denied as it exceeds the limit
    assert not rate_limiter.is_allowed(key, window_size, max_requests)

    # Sleep for 500 ms to allow all batches to slide out of window
    time.sleep((window_size + 100) / 1000)  # Sleep for 600 ms

    # Now we should be able to make a new request
    assert rate_limiter.is_allowed(key, window_size, max_requests)
