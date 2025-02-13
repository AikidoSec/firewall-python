import pytest
from .service_config import ServiceConfig
from aikido_zen.helpers.blocklist import BlockList


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
        ["127.0.0.1", "123.1.2.0/24", "132.1.0.0/16"],
        True,
        [],
    )

    # Check that non-GraphQL endpoints are correctly filtered
    assert len(service_config.endpoints) == 2
    assert service_config.endpoints[0]["route"] == "/v1"
    assert service_config.endpoints[1]["route"] == "/v3"
    assert service_config.last_updated_at == last_updated_at
    assert isinstance(service_config.bypassed_ips, BlockList)
    assert service_config.bypassed_ips.is_blocked("127.0.0.1")
    assert service_config.bypassed_ips.is_blocked("123.1.2.2")
    assert not service_config.bypassed_ips.is_blocked("1.1.1.1")
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
        blocked_ips=[],
    )


def test_initialization(service_config):
    assert len(service_config.endpoints) == 2  # Only non-graphql endpoints
    assert service_config.last_updated_at == "2023-10-01T00:00:00Z"
    assert isinstance(service_config.bypassed_ips, BlockList)
    assert service_config.blocked_uids == {"user1", "user2"}


def test_ip_blocking():
    config = ServiceConfig(
        endpoints=sample_endpoints,
        last_updated_at="2023-10-01T00:00:00Z",
        blocked_uids=["user1", "user2"],
        bypassed_ips=["192.168.1.1", "10.0.0.0/16", "::1/128"],
        received_any_stats=True,
        blocked_ips=[
            {
                "source": "geoip",
                "description": "description",
                "ips": [
                    "1.2.3.4",
                    "192.168.2.1/24",
                    "fd00:1234:5678:9abc::1",
                    "fd00:3234:5678:9abc::1/64",
                    "5.6.7.8/32",
                ],
            }
        ],
    )

    assert config.is_blocked_ip("1.2.3.4") is "description"
    assert config.is_blocked_ip("2.3.4.5") is False
    assert config.is_blocked_ip("192.168.2.2") is "description"
    assert config.is_blocked_ip("fd00:1234:5678:9abc::1") is "description"
    assert config.is_blocked_ip("fd00:1234:5678:9abc::2") is False
    assert config.is_blocked_ip("fd00:3234:5678:9abc::1") is "description"
    assert config.is_blocked_ip("fd00:3234:5678:9abc::2") is "description"
    assert config.is_blocked_ip("5.6.7.8") is "description"
    assert config.is_blocked_ip("1.2") is False

    assert config.is_bypassed_ip("192.168.1.1")
    assert config.is_bypassed_ip("10.0.0.1")
    assert config.is_bypassed_ip("10.0.1.2")
    assert config.is_bypassed_ip("10.0.254.254")
    assert config.is_bypassed_ip("::1")
    assert not config.is_bypassed_ip("::2")
    assert not config.is_bypassed_ip("1.1.1.1")
    assert not config.is_bypassed_ip("10.1.0.0")
