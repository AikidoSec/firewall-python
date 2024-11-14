import pytest
from aikido_zen.storage.service_config import ServiceConfig


@pytest.fixture
def service_config():
    endpoints = [
        {
            "graphql": True,
            "method": "POST",
            "route": "/v1",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        {
            "graphql": False,
            "method": "*",
            "route": "/posts/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        {
            "graphql": False,
            "method": "POST",
            "route": "/posts/:number",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
    ]
    last_updated_at = "2023-10-01T12:00:00Z"
    blocked_user_ids = ["user1", "user2"]
    bypassed_ips = ["192.168.1.1", "10.0.0.1"]
    received_any_stats = True

    return ServiceConfig(
        endpoints, last_updated_at, blocked_user_ids, bypassed_ips, received_any_stats
    )


def test_initialization(service_config):
    assert len(service_config.endpoints) == 2  # Only 2 endpoints should be included
    assert service_config.last_updated_at == "2023-10-01T12:00:00Z"
    assert service_config.blocked_user_ids == {"user1", "user2"}
    assert service_config.bypassed_ips == {"192.168.1.1", "10.0.0.1"}
    assert service_config.received_any_stats is True


def test_get_endpoints_with_valid_route(service_config):
    route_metadata = {
        "route": "/posts/:number",
        "url": "http://localhost:5050/posts/3",
        "method": "POST",
    }
    endpoints = service_config.get_endpoints(route_metadata)
    assert len(endpoints) == 2
    assert endpoints == [
        {
            "graphql": False,
            "method": "POST",
            "route": "/posts/:number",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        {
            "graphql": False,
            "method": "*",
            "route": "/posts/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
    ]


def test_get_endpoints_with_wildcard(service_config):
    route_metadata = {
        "route": "/posts/3/comments/10",
        "url": "/posts/3/comments/10",
        "method": "POST",
    }
    endpoints = service_config.get_endpoints(route_metadata)
    assert endpoints == [
        {
            "graphql": False,
            "method": "*",
            "route": "/posts/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
    ]


def test_get_endpoints_with_specific_method(service_config):
    route_metadata = {
        "route": "/posts/3/comments/10",
        "url": "/posts/3/comments/10",
        "method": "POST",
    }
    endpoints = service_config.get_endpoints(route_metadata)
    assert endpoints == [
        {
            "graphql": False,
            "method": "*",
            "route": "/posts/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
    ]


def test_is_bypassed_ip(service_config):
    assert service_config.is_bypassed_ip("192.168.1.1") is True
    assert service_config.is_bypassed_ip("10.0.0.2") is False


def test_is_blocked_user(service_config):
    assert service_config.is_blocked_user("user1") is True
    assert service_config.is_blocked_user("user3") is False


def test_empty_endpoints():
    empty_service_config = ServiceConfig([], "2023-10-01T12:00:00Z", [], [], False)
    assert len(empty_service_config.endpoints) == 0


def test_no_blocked_users():
    no_blocked_users_config = ServiceConfig([], "2023-10-01T12:00:00Z", [], [], False)
    assert len(no_blocked_users_config.blocked_user_ids) == 0
