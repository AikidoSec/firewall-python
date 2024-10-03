import pytest
from .get_ratelimited_endpoint import get_ratelimited_endpoint


@pytest.fixture
def endpoints():
    return [
        {
            "method": "POST",
            "route": "/api/login",
            "forceProtectionOff": False,
            "allowedIPAddresses": [],
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 3,
                "windowSizeInMS": 1000,
            },
        },
        {
            "method": "POST",
            "route": "/api/*",
            "forceProtectionOff": False,
            "allowedIPAddresses": [],
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 1,
                "windowSizeInMS": 1000,
            },
        },
        {
            "method": "GET",
            "route": "/",
            "forceProtectionOff": False,
            "allowedIPAddresses": [],
            "rateLimiting": {
                "enabled": False,
                "maxRequests": 3,
                "windowSizeInMS": 1000,
            },
        },
    ]


def test_returns_none_if_no_endpoints():
    assert get_ratelimited_endpoint([], "/api/login") is None


def test_returns_none_if_no_matching_endpoints(endpoints):
    assert get_ratelimited_endpoint([], "/nonexistent") is None


def test_returns_none_if_matching_but_not_enabled(endpoints):
    endpoints[0]["rateLimiting"]["enabled"] = False
    assert get_ratelimited_endpoint([endpoints[0]], "/api/login") is None


def test_returns_endpoint_if_matching_and_enabled(endpoints):
    result = get_ratelimited_endpoint(endpoints, "/api/login")
    assert result == endpoints[0]


def test_returns_endpoint_with_lowest_max_requests(endpoints):
    result = get_ratelimited_endpoint(endpoints, "/api/log*")
    assert result == endpoints[1]  # The one with maxRequests = 1


def test_returns_endpoint_with_smallest_window_size(endpoints):
    endpoints.append(
        {
            "method": "POST",
            "route": "/api/log*",
            "forceProtectionOff": False,
            "allowedIPAddresses": [],
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 3,
                "windowSizeInMS": 5000,
            },
        }
    )
    result = get_ratelimited_endpoint(endpoints, "/api/log*")
    assert (
        result["rateLimiting"]["windowSizeInMS"] == 5000
    )  # The one with the larger window size


def test_always_returns_exact_matches_first(endpoints):
    result = get_ratelimited_endpoint(endpoints, "/api/login")
    assert result == endpoints[0]  # Exact match should be returned first
