"""Test module for update_service_config function"""

import pytest
from unittest.mock import MagicMock, patch
from .update_service_config import update_service_config
from aikido_zen.background_process.service_config import ServiceConfig


def test_update_service_config_outbound_blocking():
    """Test that update_service_config handles outbound request blocking configuration"""

    # Create a mock connection manager with a real ServiceConfig
    connection_manager = MagicMock()
    connection_manager.conf = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )
    connection_manager.block = False

    # Test response with blockNewOutgoingRequests
    res = {
        "success": True,
        "blockNewOutgoingRequests": True,
        "domains": [
            {"hostname": "example.com", "mode": "block"},
            {"hostname": "allowed.com", "mode": "allow"},
        ],
    }

    update_service_config(connection_manager, res)

    # Verify that the outbound blocking configuration was set
    assert connection_manager.conf.block_new_outgoing_requests is True
    assert connection_manager.conf.domains == {
        "example.com": "block",
        "allowed.com": "allow",
    }


def test_update_service_config_outbound_blocking_false():
    """Test that update_service_config handles blockNewOutgoingRequests=False"""

    # Create a mock connection manager with a real ServiceConfig
    connection_manager = MagicMock()
    connection_manager.conf = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )
    connection_manager.block = True

    # Test response with blockNewOutgoingRequests=False
    res = {"success": True, "blockNewOutgoingRequests": False, "domains": []}

    update_service_config(connection_manager, res)

    # Verify that the outbound blocking configuration was set
    assert connection_manager.conf.block_new_outgoing_requests is False
    assert connection_manager.conf.domains == {}


def test_update_service_config_outbound_blocking_missing():
    """Test that update_service_config works when outbound blocking fields are missing"""

    # Create a mock connection manager with a real ServiceConfig
    connection_manager = MagicMock()
    connection_manager.conf = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )
    connection_manager.block = False

    # Test response without outbound blocking fields
    res = {
        "success": True,
        "endpoints": [],
        "configUpdatedAt": 1234567890,
    }

    update_service_config(connection_manager, res)

    # Verify that the outbound blocking configuration was not changed
    assert connection_manager.conf.block_new_outgoing_requests is False
    assert connection_manager.conf.domains == {}


def test_update_service_config_failure():
    """Test that update_service_config does nothing when response indicates failure"""

    # Create a mock connection manager with a real ServiceConfig
    connection_manager = MagicMock()
    connection_manager.conf = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )
    connection_manager.block = False

    # Set initial values
    connection_manager.conf.set_block_new_outgoing_requests(True)
    connection_manager.conf.update_domains([{"hostname": "test.com", "mode": "block"}])

    # Test failed response
    res = {"success": False, "blockNewOutgoingRequests": False, "domains": []}

    update_service_config(connection_manager, res)

    # Verify that nothing was changed due to failure
    assert connection_manager.conf.block_new_outgoing_requests is True
    assert connection_manager.conf.domains == {"test.com": "block"}


def test_update_service_config_complete():
    """Test that update_service_config handles all fields correctly"""

    # Create a mock connection manager with a real ServiceConfig
    connection_manager = MagicMock()
    connection_manager.conf = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )
    connection_manager.block = False

    # Test complete response
    res = {
        "success": True,
        "block": True,
        "endpoints": [{"route": "/test", "graphql": False}],
        "configUpdatedAt": 1234567890,
        "blockedUserIds": ["user1", "user2"],
        "allowedIPAddresses": ["192.168.1.1"],
        "receivedAnyStats": True,
        "blockNewOutgoingRequests": True,
        "domains": [
            {"hostname": "blocked.com", "mode": "block"},
            {"hostname": "allowed.com", "mode": "allow"},
            {"hostname": "test.com", "mode": "block"},
        ],
    }

    update_service_config(connection_manager, res)

    # Verify all configurations were updated
    assert connection_manager.block is True
    assert len(connection_manager.conf.endpoints) == 1
    assert connection_manager.conf.last_updated_at == 1234567890
    assert connection_manager.conf.blocked_uids == {"user1", "user2"}
    assert connection_manager.conf.received_any_stats is True
    assert connection_manager.conf.block_new_outgoing_requests is True
    assert connection_manager.conf.domains == {
        "blocked.com": "block",
        "allowed.com": "allow",
        "test.com": "block",
    }


def test_update_service_config_domains_only():
    """Test that update_service_config handles domains update only"""

    # Create a mock connection manager with a real ServiceConfig
    connection_manager = MagicMock()
    connection_manager.conf = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )
    connection_manager.block = False

    # Test response with only domains
    res = {
        "success": True,
        "domains": [
            {"hostname": "api.example.com", "mode": "block"},
            {"hostname": "cdn.example.com", "mode": "allow"},
        ],
    }

    update_service_config(connection_manager, res)

    # Verify that only domains were updated
    assert connection_manager.conf.block_new_outgoing_requests is False  # Not changed
    assert connection_manager.conf.domains == {
        "api.example.com": "block",
        "cdn.example.com": "allow",
    }


def test_update_service_config_block_new_outgoing_requests_only():
    """Test that update_service_config handles blockNewOutgoingRequests update only"""

    # Create a mock connection manager with a real ServiceConfig
    connection_manager = MagicMock()
    connection_manager.conf = ServiceConfig(
        endpoints=[],
        last_updated_at=0,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
    )
    connection_manager.block = False

    # Set initial domains
    connection_manager.conf.update_domains(
        [{"hostname": "existing.com", "mode": "allow"}]
    )

    # Test response with only blockNewOutgoingRequests
    res = {
        "success": True,
        "blockNewOutgoingRequests": True,
    }

    update_service_config(connection_manager, res)

    # Verify that only blockNewOutgoingRequests was updated
    assert connection_manager.conf.block_new_outgoing_requests is True
    assert connection_manager.conf.domains == {"existing.com": "allow"}  # Not changed
