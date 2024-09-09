import pytest
from unittest.mock import MagicMock

# Assuming the function is in a module named `rate_limiter`
from . import should_ratelimit_request


@pytest.fixture
def connection_manager():
    """Fixture to create a mock connection manager."""
    cm = MagicMock()
    cm.conf.get_endpoint.return_value = {
        "endpoint": {
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 5,
                "windowSizeInMS": 1000,
            }
        },
        "route": "/test",
    }
    cm.conf.is_bypassed_ip.return_value = False
    cm.rate_limiter.is_allowed.side_effect = (
        lambda key, window_size, max_requests: key != "GET:/test:ip:192.168.1.1"
    )
    return cm


@pytest.fixture
def route_metadata():
    """Fixture to create mock route metadata."""
    return {"method": "GET", "url": "/test"}


@pytest.fixture
def user():
    """Fixture to create a mock user."""
    return {"id": "user123"}


def test_rate_limit_ip(connection_manager, route_metadata):
    """Test that an IP is rate limited."""
    remote_address = "192.168.1.1"
    result = should_ratelimit_request(
        route_metadata, remote_address, None, connection_manager
    )
    assert result == {"block": True, "trigger": "ip"}


def test_rate_limit_user(connection_manager, route_metadata, user):
    """Test that a user is rate limited."""
    remote_address = "192.168.1.2"  # Not bypassed
    connection_manager.rate_limiter.is_allowed.side_effect = (
        lambda key, window_size, max_requests: key != "GET:/test:user:user123"
    )
    result = should_ratelimit_request(
        route_metadata, remote_address, user, connection_manager
    )
    assert result == {"block": True, "trigger": "user"}


def test_no_rate_limit(connection_manager, route_metadata):
    """Test that requests are not rate limited when not applicable."""
    remote_address = "192.168.1.3"
    connection_manager.conf.get_endpoint.return_value = None  # No matching endpoint
    result = should_ratelimit_request(
        route_metadata, remote_address, None, connection_manager
    )
    assert result == {"block": False}


def test_bypassed_ip(connection_manager, route_metadata):
    """Test that a bypassed IP is not rate limited."""
    remote_address = "192.168.1.4"
    connection_manager.conf.is_bypassed_ip.return_value = True  # Bypassed IP
    result = should_ratelimit_request(
        route_metadata, remote_address, None, connection_manager
    )
    assert result == {"block": False}


def test_rate_limit_disabled(connection_manager, route_metadata):
    """Test that rate limiting is disabled."""
    remote_address = "192.168.1.5"
    connection_manager.conf.get_endpoint.return_value = {
        "endpoint": {
            "rateLimiting": {
                "enabled": False,
                "maxRequests": 5,
                "windowSizeInMS": 1000,
            }
        },
        "route": "/test",
    }
    result = should_ratelimit_request(
        route_metadata, remote_address, None, connection_manager
    )
    assert result == {"block": False}
