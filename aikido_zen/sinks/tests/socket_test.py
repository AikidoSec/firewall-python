"""
Test module for socket sink
"""

import socket
import pytest
from unittest.mock import patch, MagicMock
import aikido_zen.sinks.socket  # Import to ensure patching
from aikido_zen.context import current_context
from aikido_zen.test_utils import generate_context
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.background_process.service_config import ServiceConfig


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    # Make sure to reset thread cache after every test
    get_cache().reset()
    current_context.set(None)


def test_socket_getaddrinfo_no_blocking():
    """Test that getaddrinfo works normally when no blocking is configured"""
    # Reset cache to ensure clean state
    get_cache().reset()

    # Test that allowed domain doesn't throw an error
    try:
        socket.getaddrinfo("localhost", 80)
    except Exception:
        pytest.fail("getaddrinfo should not throw an error for allowed domains")

    # Verify hostname was tracked
    hostnames = get_cache().hostnames.as_array()
    assert len(hostnames) == 1
    assert hostnames[0]["hostname"] == "localhost"
    assert hostnames[0]["port"] == 80
    assert hostnames[0]["hits"] == 1


def test_socket_getaddrinfo_block_specific_domain():
    """Test that getaddrinfo raises exception when specific domain is blocked"""
    # Reset cache and set up blocking for specific domain
    cache = get_cache()
    cache.reset()
    cache.config.update_domains(
        [
            {"hostname": "blocked.com", "mode": "block"},
            {"hostname": "allowed.com", "mode": "allow"},
        ]
    )

    # Test that blocked domain raises exception
    with pytest.raises(Exception) as exc_info:
        socket.getaddrinfo("blocked.com", 80)
    assert (
        "Zen has blocked an outbound connection to blocked.com"
        in str(exc_info.value)
    )

    # Test that allowed domain works normally
    socket.getaddrinfo("allowed.com", 80)

    # Verify hostnames were tracked
    hostnames = get_cache().hostnames.as_array()
    assert len(hostnames) == 2
    hostname_dict = {h["hostname"]: h for h in hostnames}
    assert "blocked.com" in hostname_dict
    assert "allowed.com" in hostname_dict
    assert hostname_dict["allowed.com"]["port"] == 80
    assert hostname_dict["allowed.com"]["hits"] == 1


def test_socket_getaddrinfo_block_all_new_requests():
    """Test that getaddrinfo raises exception when block_new_outgoing_requests is True"""
    # Reset cache and enable blocking for all new requests
    cache = get_cache()
    cache.reset()
    cache.config.set_block_new_outgoing_requests(True)
    cache.config.update_domains([{"hostname": "allowed.com", "mode": "allow"}])

    # Test that unknown domain raises exception
    with pytest.raises(Exception) as exc_info:
        socket.getaddrinfo("unknown.com", 80)
    assert (
        "Zen has blocked an outbound connection to unknown.com"
        in str(exc_info.value)
    )

    # Test that explicitly allowed domain doesn't throw an error
    try:
        socket.getaddrinfo("allowed.com", 80)
    except Exception:
        pytest.fail(
            "getaddrinfo should not throw an error for explicitly allowed domains"
        )

    # Verify hostnames were tracked
    hostnames = get_cache().hostnames.as_array()
    assert len(hostnames) == 2
    hostname_dict = {h["hostname"]: h for h in hostnames}
    assert "unknown.com" in hostname_dict
    assert "allowed.com" in hostname_dict
    assert hostname_dict["allowed.com"]["port"] == 80
    assert hostname_dict["allowed.com"]["hits"] == 1


def test_socket_getaddrinfo_no_cache():
    """Test that getaddrinfo works normally when cache is not available"""
    # Mock get_cache to return None
    with patch("aikido_zen.sinks.socket.get_cache", return_value=None):
        # Test that allowed domain doesn't throw an error when cache is unavailable
        try:
            socket.getaddrinfo("localhost", 80)
        except Exception:
            pytest.fail(
                "getaddrinfo should not throw an error when cache is unavailable"
            )


def test_service_config_should_block_outgoing_request():
    """Test the should_block_outgoing_request method"""
    config = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )

    # Test with no blocking configured
    assert not config.should_block_outgoing_request("example.com")

    # Test with specific domain blocked
    config.update_domains([{"hostname": "blocked.com", "mode": "block"}])
    assert config.should_block_outgoing_request("blocked.com")
    assert not config.should_block_outgoing_request("allowed.com")

    # Test with block_new_outgoing_requests enabled
    config.set_block_new_outgoing_requests(True)
    assert config.should_block_outgoing_request("unknown.com")  # Unknown domain blocked
    assert config.should_block_outgoing_request("blocked.com")  # Still blocked

    # Test with explicitly allowed domain when block_new_outgoing_requests is True
    config.update_domains([{"hostname": "allowed.com", "mode": "allow"}])
    assert not config.should_block_outgoing_request("allowed.com")  # Explicitly allowed
    assert config.should_block_outgoing_request("unknown.com")  # Unknown still blocked


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

    # Test updating domains
    config.update_domains(
        [
            {"hostname": "example.com", "mode": "block"},
            {"hostname": "allowed.com", "mode": "allow"},
        ]
    )
    assert config.domains == {"example.com": "block", "allowed.com": "allow"}

    # Test updating with empty list
    config.update_domains([])
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

    # Test initial state
    assert not config.block_new_outgoing_requests

    # Test setting to True
    config.set_block_new_outgoing_requests(True)
    assert config.block_new_outgoing_requests

    # Test setting to False
    config.set_block_new_outgoing_requests(False)
    assert not config.block_new_outgoing_requests


def test_socket_getaddrinfo_bypassed_ip():
    """Test that getaddrinfo works when IP is in bypassed_ips list"""
    # Reset cache and set up bypassed IPs
    cache = get_cache()
    cache.reset()
    cache.config.set_bypassed_ips(["192.168.1.0/24"])
    cache.config.set_block_new_outgoing_requests(True)
    cache.config.update_domains([{"hostname": "allowed.com", "mode": "allow"}])

    # Bypassed IP not enforced : no context
    with pytest.raises(Exception) as exc_info:
        socket.getaddrinfo("unknown.com", 80)
    assert (
        "Zen has blocked an outbound connection to unknown.com"
        in str(exc_info.value)
    )

    generate_context(ip="1.1.1.1").set_as_current_context()
    with pytest.raises(Exception) as exc_info:
        socket.getaddrinfo("unknown.com", 80)
    assert (
        "Zen has blocked an outbound connection to unknown.com"
        in str(exc_info.value)
    )

    generate_context(ip="192.168.1.80").set_as_current_context()
    try:
        socket.getaddrinfo("unknown.com", 80)
    except Exception:
        pytest.fail("getaddrinfo should not throw an error if IP is bypassed")

    # Verify hostname was tracked even when bypassed
    hostnames = get_cache().hostnames.as_array()
    assert len(hostnames) == 1  # All attempts to same hostname:port are tracked together
    assert hostnames[0]["hostname"] == "unknown.com"
    assert hostnames[0]["port"] == 80
    assert hostnames[0]["hits"] == 3  # All 3 attempts were tracked (2 blocked, 1 bypassed)


def test_socket_getaddrinfo_ip_address_as_hostname():
    """Test that getaddrinfo works when hostname is an IP address"""
    # Reset cache to ensure clean state
    get_cache().reset()

    # Test that IP address as hostname doesn't throw an error
    try:
        socket.getaddrinfo("8.8.8.8", 53)  # Google DNS
    except Exception:
        pytest.fail(
            "getaddrinfo should not throw an error for IP addresses as hostnames"
        )

    # Verify IP address was tracked as hostname
    hostnames = get_cache().hostnames.as_array()
    assert len(hostnames) == 1
    assert hostnames[0]["hostname"] == "8.8.8.8"
    assert hostnames[0]["port"] == 53
    assert hostnames[0]["hits"] == 1


def test_socket_getaddrinfo_blocked_punycode_hostname():
    """Test that getaddrinfo blocks when punycode hostname is explicitly blocked"""
    # Reset cache and set up blocking for specific punycode domain
    cache = get_cache()
    cache.reset()
    cache.config.update_domains(
        [
            {"hostname": "xn--blocked-7ta.com", "mode": "block"},
            {"hostname": "xn--allowed-8ta.com", "mode": "allow"},
        ]
    )

    # Test that blocked punycode domain raises exception
    with pytest.raises(Exception) as exc_info:
        socket.getaddrinfo("xn--blocked-7ta.com", 80)
    assert (
        "Zen has blocked an outbound connection: socket.getaddrinfo to xn--blocked-7ta.com"
        in str(exc_info.value)
    )

    # Test that allowed punycode domain works normally
    try:
        socket.getaddrinfo("xn--allowed-8ta.com", 80)
    except Exception as e:
        assert not "Zen has blocked an outbound connection" in str(e)
