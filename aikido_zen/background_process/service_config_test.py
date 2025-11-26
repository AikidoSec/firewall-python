import pytest
from .service_config import ServiceConfig
from aikido_zen.helpers.ip_matcher import IPMatcher


def test_service_config_initialization():
    service_config = ServiceConfig()
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
        {
            "graphql": False,
            "method": "GET",
            "route": "/admin",
            "rate_limiting": {
                "enabled": False,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "allowedIPAddresses": ["1.2.3.4", "192.168.2.0/24"],
            "force_protection_off": False,
        },
    ]

    assert len(service_config.endpoints) == 0
    service_config.set_endpoints(endpoints)
    assert (
        len(service_config.endpoints) == 3
    )  # Check that non-GraphQL endpoints are correctly filtered
    assert service_config.endpoints[0]["route"] == "/v1"
    assert service_config.endpoints[1]["route"] == "/v3"
    assert service_config.endpoints[2]["route"] == "/admin"

    service_config.set_last_updated_at(37982562953)
    assert service_config.last_updated_at == 37982562953

    assert isinstance(service_config.bypassed_ips, IPMatcher)
    service_config.set_bypassed_ips(["127.0.0.1", "123.1.2.0/24", "132.1.0.0/16"])
    assert isinstance(service_config.bypassed_ips, IPMatcher)
    assert service_config.bypassed_ips.has("127.0.0.1")
    assert service_config.bypassed_ips.has("123.1.2.2")
    assert not service_config.bypassed_ips.has("1.1.1.1")

    assert len(service_config.blocked_uids) == 0
    service_config.set_blocked_user_ids({"0", "0", "1", "5"})
    assert service_config.blocked_uids == {"1", "0", "5"}

    assert not service_config.received_any_stats
    service_config.enable_received_any_stats()
    assert service_config.received_any_stats == True

    v1_endpoint = service_config.get_endpoints(
        {
            "method": "POST",
            "route": "/v1",
            "url": "/v1",
        }
    )[0]
    assert v1_endpoint["route"] == "/v1"
    assert not "allowedIPAddresses" in v1_endpoint

    admin_endpoint = service_config.get_endpoints(
        {
            "method": "GET",
            "route": "/admin",
            "url": "/admin",
        }
    )[0]
    assert admin_endpoint["route"] == "/admin"
    assert isinstance(admin_endpoint["allowedIPAddresses"], IPMatcher)
    assert admin_endpoint["allowedIPAddresses"].has("192.168.2.1")
    assert admin_endpoint["allowedIPAddresses"].has("1.2.3.4")
    assert not admin_endpoint["allowedIPAddresses"].has("192.168.0.1")


def test_ip_blocking():
    config = ServiceConfig()
    config.set_bypassed_ips(["192.168.1.1", "10.0.0.0/16", "::1/128"])
    assert config.is_bypassed_ip("192.168.1.1")
    assert config.is_bypassed_ip("10.0.0.1")
    assert config.is_bypassed_ip("10.0.1.2")
    assert config.is_bypassed_ip("10.0.254.254")
    assert config.is_bypassed_ip("::1")
    assert not config.is_bypassed_ip("::2")
    assert not config.is_bypassed_ip("1.1.1.1")
    assert not config.is_bypassed_ip("10.1.0.0")


def test_service_config_with_empty_allowlist():
    service_config = ServiceConfig()

    # Check that non-GraphQL endpoints are correctly filtered
    service_config.set_endpoints(
        [
            {
                "graphql": False,
                "method": "GET",
                "route": "/admin",
                "rate_limiting": {
                    "enabled": False,
                    "max_requests": 10,
                    "window_size_in_ms": 1000,
                },
                "allowedIPAddresses": [],
                "force_protection_off": False,
            },
        ]
    )
    assert len(service_config.endpoints) == 1
    assert service_config.endpoints[0]["route"] == "/admin"

    service_config.set_last_updated_at(29839537)
    assert service_config.last_updated_at == 29839537

    service_config.set_blocked_user_ids({"0", "0", "1", "5"})
    assert service_config.blocked_uids == {"1", "0", "5"}

    service_config.set_bypassed_ips(["127.0.0.1", "123.1.2.0/24", "132.1.0.0/16"])
    assert isinstance(service_config.bypassed_ips, IPMatcher)
    assert service_config.is_bypassed_ip("127.0.0.1")
    assert service_config.is_bypassed_ip("123.1.2.2")
    assert not service_config.is_bypassed_ip("1.1.1.1")

    admin_endpoint = service_config.get_endpoints(
        {
            "method": "GET",
            "route": "/admin",
            "url": "/admin",
        }
    )[0]
    assert admin_endpoint["route"] == "/admin"
    assert isinstance(admin_endpoint["allowedIPAddresses"], list)
    assert len(admin_endpoint["allowedIPAddresses"]) == 0
