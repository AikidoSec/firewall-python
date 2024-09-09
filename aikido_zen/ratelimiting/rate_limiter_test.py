import pytest
import time
from .rate_limiter import RateLimiter

# Assuming the RateLimiter class is defined above


@pytest.fixture
def rate_limiter():
    max_amount = 5
    ttl = 500  # 0.5 seconds
    return RateLimiter(max_amount, ttl)


def test_allow_up_to_max_amount_requests_within_ttl(rate_limiter):
    key = "user1"
    for i in range(rate_limiter.max_items):
        assert rate_limiter.is_allowed(
            key, rate_limiter.time_to_live_in_ms, rate_limiter.max_items
        ), f"Request {i + 1} should be allowed"

    assert not rate_limiter.is_allowed(
        key, rate_limiter.time_to_live_in_ms, rate_limiter.max_items
    ), "Request 6 should not be allowed"


def test_reset_after_ttl_expired(rate_limiter):
    key = "user1"
    for i in range(rate_limiter.max_items):
        assert rate_limiter.is_allowed(
            key, rate_limiter.time_to_live_in_ms, rate_limiter.max_items
        ), f"Request {i + 1} should be allowed"

    assert not rate_limiter.is_allowed(
        key, rate_limiter.time_to_live_in_ms, rate_limiter.max_items
    ), "Request 6 should not be allowed"

    # Simulate the passage of time
    time.sleep(
        (rate_limiter.time_to_live_in_ms / 1000) + 0.1
    )  # Convert ms to seconds and add a small buffer

    assert rate_limiter.is_allowed(
        key, rate_limiter.time_to_live_in_ms, rate_limiter.max_items
    ), "Request after TTL should be allowed"


def test_allow_requests_for_different_keys_independently(rate_limiter):
    key1 = "user1"
    key2 = "user2"

    for i in range(rate_limiter.max_items):
        assert rate_limiter.is_allowed(
            key1, rate_limiter.time_to_live_in_ms, rate_limiter.max_items
        ), f"Request {i + 1} for key1 should be allowed"

    assert not rate_limiter.is_allowed(
        key1, rate_limiter.time_to_live_in_ms, rate_limiter.max_items
    ), "Request 6 for key1 should not be allowed"

    for i in range(rate_limiter.max_items):
        assert rate_limiter.is_allowed(
            key2, rate_limiter.time_to_live_in_ms, rate_limiter.max_items
        ), f"Request {i + 1} for key2 should be allowed"

    assert not rate_limiter.is_allowed(
        key2, rate_limiter.time_to_live_in_ms, rate_limiter.max_items
    ), "Request 6 for key2 should not be allowed"


# To run the tests, you would typically use the command line:
# pytest test_ratelimiter.py
