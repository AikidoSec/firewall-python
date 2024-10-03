import pytest
from unittest.mock import MagicMock
from aikido_zen.background_process.service_config import ServiceConfig
from aikido_zen.ratelimiting.rate_limiter import RateLimiter
from . import should_ratelimit_request


def create_route_metadata(method="POST", route="/login"):
    return {"method": method, "url": route, "route": route}


@pytest.fixture
def user():
    """Fixture to create a mock user."""
    return {"id": "user123"}


def create_connection_manager(endpoints=[], bypassed_ips=[]):
    cm = MagicMock()
    cm.conf = ServiceConfig(
        endpoints=endpoints,
        last_updated_at=1,
        blocked_uids=[],
        bypassed_ips=bypassed_ips,
        received_any_stats=True,
    )
    cm.rate_limiter = RateLimiter(
        max_items=5000, time_to_live_in_ms=120 * 60 * 1000  # 120 minutes
    )
    return cm


def test_rate_limits_by_ip():
    cm = create_connection_manager(
        [
            {
                "method": "POST",
                "route": "/login",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 3,
                    "windowSizeInMS": 1000,
                },
            },
        ]
    )
    route_metadata = create_route_metadata()
    assert should_ratelimit_request(route_metadata, "1.2.3.4", None, cm) == {
        "block": False
    }
    assert should_ratelimit_request(route_metadata, "1.2.3.4", None, cm) == {
        "block": False
    }
    assert should_ratelimit_request(route_metadata, "1.2.3.4", None, cm) == {
        "block": False
    }
    assert should_ratelimit_request(route_metadata, "1.2.3.4", None, cm) == {
        "block": True,
        "trigger": "ip",
    }


def test_rate_limiting_ip_allowed():
    cm = create_connection_manager(
        [
            {
                "method": "POST",
                "route": "/login",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 3,
                    "windowSizeInMS": 1000,
                },
            },
        ],
        ["1.2.3.4"],
    )

    # Test requests from allowed IP
    route_metadata = create_route_metadata()
    assert should_ratelimit_request(route_metadata, "1.2.3.4", None, cm) == {
        "block": False
    }
    assert should_ratelimit_request(route_metadata, "1.2.3.4", None, cm) == {
        "block": False
    }
    assert should_ratelimit_request(route_metadata, "1.2.3.4", None, cm) == {
        "block": False
    }
    assert should_ratelimit_request(route_metadata, "1.2.3.4", None, cm) == {
        "block": False
    }


def test_rate_limiting_by_user(user):
    cm = create_connection_manager(
        [
            {
                "method": "POST",
                "route": "/login",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 3,
                    "windowSizeInMS": 1000,
                },
            },
        ]
    )

    # Test requests from the same user
    route_metadata = create_route_metadata()
    assert should_ratelimit_request(route_metadata, "1.2.3.4", user, cm) == {
        "block": False
    }
    assert should_ratelimit_request(route_metadata, "1.2.3.5", user, cm) == {
        "block": False
    }
    assert should_ratelimit_request(route_metadata, "1.2.3.6", user, cm) == {
        "block": False
    }
    assert should_ratelimit_request(route_metadata, "1.2.3.7", user, cm) == {
        "block": True,
        "trigger": "user",
    }


def test_rate_limiting_with_wildcard():
    cm = create_connection_manager(
        [
            {
                "method": "POST",
                "route": "/api/*",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 3,
                    "windowSizeInMS": 1000,
                },
            },
        ]
    )

    # Test requests to different API endpoints
    assert should_ratelimit_request(
        create_route_metadata(route="/api/login"), "1.2.3.4", None, cm
    ) == {"block": False}
    assert should_ratelimit_request(
        create_route_metadata(route="/api/logout"), "1.2.3.4", None, cm
    ) == {"block": False}
    assert should_ratelimit_request(
        create_route_metadata(route="/api/reset-password"), "1.2.3.4", None, cm
    ) == {"block": False}

    # This request should trigger the rate limit
    assert should_ratelimit_request(
        create_route_metadata(route="/api/login"), "1.2.3.4", None, cm
    ) == {"block": True, "trigger": "ip"}


def test_rate_limiting_with_wildcard2():
    cm = create_connection_manager(
        [
            {
                "method": "*",
                "route": "/api/*",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 3,
                    "windowSizeInMS": 1000,
                },
            },
        ]
    )

    # Test requests to different API endpoints with various methods
    metadata = create_route_metadata(route="/api/login", method="POST")
    assert should_ratelimit_request(metadata, "1.2.3.4", None, cm) == {"block": False}

    metadata = create_route_metadata(route="/api/logout", method="GET")
    assert should_ratelimit_request(metadata, "1.2.3.4", None, cm) == {"block": False}

    metadata = create_route_metadata(route="/api/reset-password", method="PUT")
    assert should_ratelimit_request(metadata, "1.2.3.4", None, cm) == {"block": False}

    # This request should trigger the rate limit
    metadata = create_route_metadata(route="/api/login", method="GET")
    assert should_ratelimit_request(metadata, "1.2.3.4", None, cm) == {
        "block": True,
        "trigger": "ip",
    }
