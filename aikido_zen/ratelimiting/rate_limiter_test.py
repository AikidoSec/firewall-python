import random
import time
from unittest.mock import patch

import pytest
from .rate_limiter import RateLimiter


@pytest.fixture
def rate_limiter():
    max_items = 10
    time_to_live_in_ms = 1000  # 1 second TTL
    return RateLimiter(max_items, time_to_live_in_ms)


def test_allow_requests_within_limit(rate_limiter):
    key = "user1"
    for i in range(5):
        assert rate_limiter.record_request(key, 5000000, 5)[
            "allowed"
        ], f"Request {i + 1} should be allowed"


def test_deny_requests_exceeding_limit(rate_limiter):
    key = "user2"
    for i in range(5):
        rate_limiter.record_request(key, 500, 5)
    assert not rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "Request 6 should not be allowed"


def test_clear_old_entries(rate_limiter):
    key = "user3"
    for i in range(5):
        rate_limiter.record_request(key, 500, 5)

    time.sleep(0.6)  # Sleep to allow old entries to be cleared

    assert rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "New request should be allowed after clearing old entries"


def test_multiple_keys(rate_limiter):
    key1 = "user4"
    key2 = "user5"

    for i in range(5):
        assert rate_limiter.record_request(key1, 500, 5)[
            "allowed"
        ], f"Request {i + 1} for key1 should be allowed"
    for i in range(5):
        assert rate_limiter.record_request(key2, 500, 5)[
            "allowed"
        ], f"Request {i + 1} for key2 should be allowed"

    assert not rate_limiter.record_request(key1, 500, 5)[
        "allowed"
    ], "Request 6 for key1 should not be allowed"
    assert not rate_limiter.record_request(key2, 500, 5)[
        "allowed"
    ], "Request 6 for key2 should not be allowed"


def test_ttl_expiration(rate_limiter):
    key = "user6"
    for i in range(5):
        rate_limiter.record_request(key, 500, 5)

    time.sleep(1.1)  # Sleep to allow the TTL to expire

    assert rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "Request after TTL should be allowed"


def test_allow_requests_exactly_at_limit(rate_limiter):
    key = "user7"
    for i in range(5):
        assert rate_limiter.record_request(key, 500, 5)[
            "allowed"
        ], f"Request {i + 1} should be allowed"
    assert not rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "Request 6 should not be allowed"


def test_allow_requests_after_clearing_old_entries(rate_limiter):
    key = "user8"
    for i in range(5):
        rate_limiter.record_request(key, 500, 5)

    time.sleep(0.6)  # Sleep to allow old entries to be cleared

    assert rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "New request should be allowed after clearing old entries"


def test_multiple_rapid_requests(rate_limiter):
    key = "user9"
    for i in range(5):
        assert rate_limiter.record_request(key, 500, 5)[
            "allowed"
        ], f"Request {i + 1} should be allowed"

    time.sleep(0.1)  # Sleep for 100 ms

    assert not rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "Request after rapid requests should not be allowed"


def test_reset_after_ttl(rate_limiter):
    key = "user10"
    for i in range(5):
        rate_limiter.record_request(key, 500, 5)

    time.sleep(1.1)  # Sleep to allow the TTL to expire

    assert rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "Request after TTL should be allowed"


def test_different_window_sizes(rate_limiter):
    key = "user11"
    different_window_size = 1000  # 1 second window
    for i in range(5):
        assert rate_limiter.record_request(key, different_window_size, 5)[
            "allowed"
        ], f"Request {i + 1} should be allowed"
    assert not rate_limiter.record_request(key, different_window_size, 5)[
        "allowed"
    ], "Request 6 should not be allowed"


def test_sliding_window_with_intermittent_requests(rate_limiter):
    key = "user14"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.record_request(key, 500, 5)[
            "allowed"
        ], f"Request {i + 1} should be allowed"
        time.sleep(0.1)  # Sleep 100 ms between requests

    # Sleep for 600 ms to allow the first requests to slide out of the window
    time.sleep(0.6)

    # Now we should be able to make a new request
    assert rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "New request should be allowed after sliding"


def test_sliding_window_edge_case(rate_limiter):
    key = "user15"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.record_request(key, 500, 5)[
            "allowed"
        ], f"Request {i + 1} should be allowed"

    # Sleep for 500 ms to simulate time passing
    time.sleep(0.6)

    # The next request should still be allowed as the window is sliding
    assert rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "Next request should be allowed as window slides"

    # Sleep for another 500 ms to allow the first batch to expire
    time.sleep(0.6)

    # Now we should be able to make a new request
    assert rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "New request should be allowed after first batch expires"


def test_sliding_window_with_burst_requests(rate_limiter):
    key = "user16"
    window_size_ms = 500

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.record_request(key, window_size_ms, 5)[
            "allowed"
        ], f"Request {i + 1} should be allowed"

    # Sleep for 250 ms to simulate time passing
    time.sleep((window_size_ms / 2) / 1000)

    # Add 3 more requests (should be denied)
    assert not rate_limiter.record_request(key, window_size_ms, 5)[
        "allowed"
    ], "Request should not be allowed"
    assert not rate_limiter.record_request(key, window_size_ms, 5)[
        "allowed"
    ], "Request should not be allowed"
    assert not rate_limiter.record_request(key, window_size_ms, 5)[
        "allowed"
    ], "Request should not be allowed"

    time.sleep(
        (window_size_ms / 2 + 50) / 1000
    )  # 50ms buffer, first requests are still in window

    # Make a burst of requests (should be allowed)
    for i in range(2):
        assert rate_limiter.record_request(key, window_size_ms, 5)[
            "allowed"
        ], f"Burst request {i + 1} should be allowed"
    assert not rate_limiter.record_request(key, window_size_ms, 5)[
        "allowed"
    ], "Burst request should not be allowed after limit"

    # Sleep for 500 ms to allow all batches to slide out of window
    time.sleep((window_size_ms + 100) / 1000)

    # Now we should be able to make a new request
    assert rate_limiter.record_request(key, window_size_ms, 5)[
        "allowed"
    ], "New request should be allowed after all batches slide out"


def test_sliding_window_with_delayed_requests(rate_limiter):
    key = "user17"

    # Allow 5 requests in a 1-second window
    for i in range(5):
        assert rate_limiter.record_request(key, 500, 5)[
            "allowed"
        ], f"Request {i + 1} should be allowed"
        time.sleep(0.1)  # Sleep 100 ms between requests

    # Sleep for 600 ms to allow the first requests to slide out of the window
    time.sleep(0.6)

    # Now we should be able to make a new request
    assert rate_limiter.record_request(key, 500, 5)[
        "allowed"
    ], "New request should be allowed after sliding"


@pytest.fixture
def clock():
    current = {"time_in_ms": 0}
    with patch(
        "aikido_zen.ratelimiting.rate_limiter.get_unixtime_ms",
        side_effect=lambda: current["time_in_ms"],
    ):
        yield current


def new_rate_limiter():
    return RateLimiter(max_items=10, time_to_live_in_ms=120 * 60 * 1000)


def send_requests(
    clock, rate_limiter, times_in_ms, max_requests=3, window_size_in_ms=60_000
):
    results = []
    for time_in_ms in times_in_ms:
        clock["time_in_ms"] = time_in_ms
        results.append(
            rate_limiter.record_request("key", window_size_in_ms, max_requests)
        )
    return results


def test_retry_after_counts_the_blocked_request(clock):
    history = [0, 20_000, 40_000, 50_000]
    assert send_requests(clock, new_rate_limiter(), history) == [
        {"allowed": True},
        {"allowed": True},
        {"allowed": True},
        {"allowed": False, "retry_after_seconds": 31},
    ]

    assert (
        send_requests(clock, new_rate_limiter(), history + [80_000])[-1]["allowed"]
        is False
    )
    assert send_requests(clock, new_rate_limiter(), history + [81_000])[-1] == {
        "allowed": True
    }


def test_retry_after_counts_every_blocked_request(clock):
    history = [0, 20_000, 40_000, 50_000, 55_000]
    assert send_requests(clock, new_rate_limiter(), history)[-2:] == [
        {"allowed": False, "retry_after_seconds": 31},
        {"allowed": False, "retry_after_seconds": 46},
    ]

    assert (
        send_requests(clock, new_rate_limiter(), history + [100_000])[-1]["allowed"]
        is False
    )
    assert send_requests(clock, new_rate_limiter(), history + [101_000])[-1] == {
        "allowed": True
    }


def test_retry_after_for_requests_in_the_same_millisecond(clock):
    history = [0, 0, 0, 0]
    assert send_requests(clock, new_rate_limiter(), history)[-1] == {
        "allowed": False,
        "retry_after_seconds": 61,
    }

    assert (
        send_requests(clock, new_rate_limiter(), history + [60_000])[-1]["allowed"]
        is False
    )
    assert send_requests(clock, new_rate_limiter(), history + [61_000])[-1] == {
        "allowed": True
    }


def test_retry_after_is_the_shortest_wait_that_allows_a_retry(clock):
    rng = random.Random(0)
    blocked_histories = 0
    for _ in range(1000):
        max_requests = rng.randint(1, 6)
        window_size_in_ms = rng.choice([1000, 5000, 60_000])
        history = [0]
        for _ in range(rng.randint(1, 15)):
            history.append(history[-1] + rng.choice([0, 1, rng.randint(0, 30_000)]))

        last = send_requests(
            clock, new_rate_limiter(), history, max_requests, window_size_in_ms
        )[-1]
        if last["allowed"]:
            continue
        blocked_histories += 1

        for wait_in_seconds, expected in [
            (last["retry_after_seconds"], True),
            (last["retry_after_seconds"] - 1, False),
        ]:
            retry_at = history[-1] + wait_in_seconds * 1000
            retry = send_requests(
                clock,
                new_rate_limiter(),
                history + [retry_at],
                max_requests,
                window_size_in_ms,
            )[-1]
            assert retry["allowed"] is expected, (
                history,
                max_requests,
                window_size_in_ms,
            )
    assert blocked_histories > 400


@pytest.mark.parametrize(
    "max_requests, window_size_in_ms",
    [(0, 60_000), (-1, 60_000), (0, -1000)],
)
def test_no_retry_after_when_no_request_can_be_allowed(
    clock, max_requests, window_size_in_ms
):
    assert (
        send_requests(
            clock, new_rate_limiter(), [0, 1000], max_requests, window_size_in_ms
        )
        == [{"allowed": False, "retry_after_seconds": None}] * 2
    )
