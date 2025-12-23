import pytest
from .service_config import ServiceConfig
from aikido_zen.helpers.ip_matcher import IPMatcher


def test_service_config_outbound_blocking_initialization():
    """Test that ServiceConfig initializes outbound blocking fields correctly"""
    config = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )

    # Test initial values
    assert hasattr(config, "block_new_outgoing_requests")
    assert hasattr(config, "domains")
    assert config.block_new_outgoing_requests is False
    assert config.domains == {}


def test_service_config_set_block_new_outgoing_requests():
    """Test the set_block_new_outgoing_requests method"""
    config = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )

    # Test setting to True
    config.set_block_new_outgoing_requests(True)
    assert config.block_new_outgoing_requests is True

    # Test setting to False
    config.set_block_new_outgoing_requests(False)
    assert config.block_new_outgoing_requests is False

    # Test setting with non-boolean values
    config.set_block_new_outgoing_requests(1)
    assert config.block_new_outgoing_requests is True

    config.set_block_new_outgoing_requests(0)
    assert config.block_new_outgoing_requests is False

    config.set_block_new_outgoing_requests("true")
    assert config.block_new_outgoing_requests is True

    config.set_block_new_outgoing_requests("")
    assert config.block_new_outgoing_requests is False


def test_service_config_update_domains():
    """Test the update_domains method"""
    config = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )

    # Test initial state
    assert config.domains == {}

    # Test updating with domains
    domains_data = [
        {"hostname": "example.com", "mode": "block"},
        {"hostname": "allowed.com", "mode": "allow"},
        {"hostname": "test.com", "mode": "block"},
    ]
    config.update_domains(domains_data)
    assert config.domains == {
        "example.com": "block",
        "allowed.com": "allow",
        "test.com": "block",
    }

    # Test updating with empty list
    config.update_domains([])
    assert config.domains == {}

    # Test updating with single domain
    config.update_domains([{"hostname": "single.com", "mode": "allow"}])
    assert config.domains == {"single.com": "allow"}


def test_service_config_should_block_outgoing_request():
    """Test the should_block_outgoing_request method"""
    config = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )

    # Test with block_new_outgoing_requests = False (default)
    # Only block if mode is "block"
    config.update_domains(
        [
            {"hostname": "blocked.com", "mode": "block"},
            {"hostname": "allowed.com", "mode": "allow"},
        ]
    )

    assert config.should_block_outgoing_request("blocked.com") is True
    assert config.should_block_outgoing_request("allowed.com") is False
    assert (
        config.should_block_outgoing_request("unknown.com") is False
    )  # Unknown = allowed

    # Test with block_new_outgoing_requests = True
    config.set_block_new_outgoing_requests(True)
    # Only allow if mode is "allow", block everything else
    assert config.should_block_outgoing_request("blocked.com") is True  # Still blocked
    assert (
        config.should_block_outgoing_request("allowed.com") is False
    )  # Explicitly allowed
    assert (
        config.should_block_outgoing_request("unknown.com") is True
    )  # Unknown = blocked

    # Test edge cases
    config.set_block_new_outgoing_requests(False)
    config.update_domains([])  # No domains configured
    assert (
        config.should_block_outgoing_request("any.com") is False
    )  # No blocking when no domains

    config.set_block_new_outgoing_requests(True)
    config.update_domains([])  # No domains configured
    assert (
        config.should_block_outgoing_request("any.com") is True
    )  # Block all when block_new_outgoing_requests=True


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
    last_updated_at = "2023-10-01"
    service_config = ServiceConfig(
        endpoints,
        last_updated_at,
        ["0", "0", "1", "5"],
        ["127.0.0.1", "123.1.2.0/24", "132.1.0.0/16"],
        True,
    )

    # Check that non-GraphQL endpoints are correctly filtered
    assert len(service_config.endpoints) == 3
    assert service_config.endpoints[0]["route"] == "/v1"
    assert service_config.endpoints[1]["route"] == "/v3"
    assert service_config.endpoints[2]["route"] == "/admin"
    assert service_config.last_updated_at == last_updated_at
    assert isinstance(service_config.bypassed_ips, IPMatcher)
    assert service_config.bypassed_ips.has("127.0.0.1")
    assert service_config.bypassed_ips.has("123.1.2.2")
    assert not service_config.bypassed_ips.has("1.1.1.1")
    assert service_config.blocked_uids == set(["1", "0", "5"])

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
    assert isinstance(service_config.bypassed_ips, IPMatcher)
    assert service_config.blocked_uids == {"user1", "user2"}


def test_ip_blocking():
    config = ServiceConfig(
        endpoints=sample_endpoints,
        last_updated_at="2023-10-01T00:00:00Z",
        blocked_uids=["user1", "user2"],
        bypassed_ips=["192.168.1.1", "10.0.0.0/16", "::1/128"],
        received_any_stats=True,
    )

    assert config.is_bypassed_ip("192.168.1.1")
    assert config.is_bypassed_ip("10.0.0.1")
    assert config.is_bypassed_ip("10.0.1.2")
    assert config.is_bypassed_ip("10.0.254.254")
    assert config.is_bypassed_ip("::1")
    assert not config.is_bypassed_ip("::2")
    assert not config.is_bypassed_ip("1.1.1.1")
    assert not config.is_bypassed_ip("10.1.0.0")


def test_service_config_with_empty_allowlist():
    endpoints = [
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
    last_updated_at = "2023-10-01"
    service_config = ServiceConfig(
        endpoints,
        last_updated_at,
        ["0", "0", "1", "5"],
        ["127.0.0.1", "123.1.2.0/24", "132.1.0.0/16"],
        True,
    )

    # Check that non-GraphQL endpoints are correctly filtered
    assert len(service_config.endpoints) == 1
    assert service_config.endpoints[0]["route"] == "/admin"
    assert service_config.last_updated_at == last_updated_at
    assert isinstance(service_config.bypassed_ips, IPMatcher)
    assert service_config.bypassed_ips.has("127.0.0.1")
    assert service_config.bypassed_ips.has("123.1.2.2")
    assert not service_config.bypassed_ips.has("1.1.1.1")
    assert service_config.blocked_uids == set(["1", "0", "5"])

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
