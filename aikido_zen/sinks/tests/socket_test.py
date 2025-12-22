"""
Test module for socket sink
"""

import importlib
import socket
import pytest
from unittest.mock import patch, MagicMock
import aikido_zen.sinks.socket  # Import to ensure patching
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.background_process.service_config import ServiceConfig


def test_socket_getaddrinfo_no_blocking():
    """Test that getaddrinfo works normally when no blocking is configured"""
    # Reset cache to ensure clean state
    get_cache().reset()

    # Test that allowed domain doesn't throw an error
    try:
        socket.getaddrinfo("example.com", 80)
    except Exception:
        pytest.fail("getaddrinfo should not throw an error for allowed domains")


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
        "Zen has blocked an outbound connection: socket.getaddrinfo to blocked.com"
        in str(exc_info.value)
    )

    # Test that allowed domain works normally
    socket.getaddrinfo("allowed.com", 80)


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
        "Zen has blocked an outbound connection: socket.getaddrinfo to unknown.com"
        in str(exc_info.value)
    )

    # Test that explicitly allowed domain doesn't throw an error
    try:
        socket.getaddrinfo("allowed.com", 80)
    except Exception:
        pytest.fail(
            "getaddrinfo should not throw an error for explicitly allowed domains"
        )


def test_socket_getaddrinfo_no_cache():
    """Test that getaddrinfo works normally when cache is not available"""
    # Mock get_cache to return None
    with patch("aikido_zen.sinks.socket.get_cache", return_value=None):
        # Test that allowed domain doesn't throw an error when cache is unavailable
        try:
            socket.getaddrinfo("example.com", 80)
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
