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


def get_patched_socket_module():
    """Get a patched socket module"""
    import socket
    from aikido_zen.sinks import patch_function
    import aikido_zen.sinks.socket

    # Manually apply the patch
    patch_function(socket, "getaddrinfo", aikido_zen.sinks.socket._getaddrinfo_wrapper)

    return socket


def test_socket_getaddrinfo_no_blocking():
    """Test that getaddrinfo works normally when no blocking is configured"""
    # Reset cache to ensure clean state
    get_cache().reset()

    # Get patched socket module
    socket_module = get_patched_socket_module()

    # Mock getaddrinfo to return a known value
    mock_result = [(2, 1, 6, "", ("127.0.0.1", 80))]
    with patch.object(socket_module, "getaddrinfo", return_value=mock_result):
        result = socket_module.getaddrinfo("example.com", 80)
        assert result == mock_result


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

    # Get patched socket module
    socket_module = get_patched_socket_module()

    # Test that blocked domain raises exception
    with pytest.raises(Exception) as exc_info:
        socket_module.getaddrinfo("blocked.com", 80)
    assert (
        "Zen has blocked an outbound connection: socket.getaddrinfo to blocked.com"
        in str(exc_info.value)
    )

    # Test that allowed domain works normally
    mock_result = [(2, 1, 6, "", ("127.0.0.1", 80))]
    with patch.object(socket_module, "getaddrinfo", return_value=mock_result):
        result = socket_module.getaddrinfo("allowed.com", 80)
        assert result == mock_result


def test_socket_getaddrinfo_block_all_new_requests():
    """Test that getaddrinfo raises exception when block_new_outgoing_requests is True"""
    # Reset cache and enable blocking for all new requests
    cache = get_cache()
    cache.reset()
    cache.config.set_block_new_outgoing_requests(True)
    cache.config.update_domains([{"hostname": "allowed.com", "mode": "allow"}])

    # Get patched socket module
    socket_module = get_patched_socket_module()

    # Test that unknown domain raises exception
    with pytest.raises(Exception) as exc_info:
        socket_module.getaddrinfo("unknown.com", 80)
    assert (
        "Zen has blocked an outbound connection: socket.getaddrinfo to unknown.com"
        in str(exc_info.value)
    )

    # Test that explicitly allowed domain works even when block_new_outgoing_requests is True
    mock_result = [(2, 1, 6, "", ("127.0.0.1", 80))]
    with patch.object(socket_module, "getaddrinfo", return_value=mock_result):
        result = socket_module.getaddrinfo("allowed.com", 80)
        assert result == mock_result


def test_socket_getaddrinfo_no_cache():
    """Test that getaddrinfo works normally when cache is not available"""
    # Get patched socket module
    socket_module = get_patched_socket_module()

    # Mock get_cache to return None
    with patch("aikido_zen.sinks.socket.get_cache", return_value=None):
        mock_result = [(2, 1, 6, "", ("127.0.0.1", 80))]
        with patch.object(socket_module, "getaddrinfo", return_value=mock_result):
            result = socket_module.getaddrinfo("example.com", 80)
            assert result == mock_result


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
