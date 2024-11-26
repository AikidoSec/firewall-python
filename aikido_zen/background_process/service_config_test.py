import pytest
from .service_config import ServiceConfig


def test_service_config_initialization():
    endpoints = [
        {
            "graphql": False,
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
            "graphql": True,
            "method": "POST",
            "route": "/v2",
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
            "route": "/v3",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
    ]
    last_updated_at = "2023-10-01"
    service_config = ServiceConfig(
        endpoints,
        last_updated_at,
        ["0", "0", "1", "5"],
        ["5", "1", "2", "1", "5"],
        True,
    )

    # Check that non-GraphQL endpoints are correctly filtered
    assert len(service_config.endpoints) == 2
    assert service_config.endpoints[0]["route"] == "/v1"
    assert service_config.endpoints[1]["route"] == "/v3"
    assert service_config.last_updated_at == last_updated_at
    assert service_config.bypassed_ips == set(["1", "2", "5"])
    assert service_config.blocked_uids == set(["1", "0", "5"])


# Sample data for testing
sample_endpoints = [
    {"url": "http://example.com/api/v1", "graphql": False, "context": "user"},
    {"url": "http://example.com/api/v2", "graphql": True, "context": "admin"},
    {"url": "http://example.com/api/v3", "graphql": False, "context": "guest"},
]


@pytest.fixture
def service_config():
    return ServiceConfig(
        endpoints=sample_endpoints,
        last_updated_at="2023-10-01T00:00:00Z",
        blocked_uids=["user1", "user2"],
        bypassed_ips=["192.168.1.1", "10.0.0.1"],
        received_any_stats=True,
    )


def test_initialization(service_config):
    assert len(service_config.endpoints) == 2  # Only non-graphql endpoints
    assert service_config.last_updated_at == "2023-10-01T00:00:00Z"
    assert service_config.bypassed_ips == {"192.168.1.1", "10.0.0.1"}
    assert service_config.blocked_uids == {"user1", "user2"}
