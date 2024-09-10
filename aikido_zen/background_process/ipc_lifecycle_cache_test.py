import pytest
from unittest.mock import MagicMock, patch
from .ipc_lifecycle_cache import IPCLifecycleCache, get_cache


@pytest.fixture
def mock_context():
    """Fixture to create a mock context."""
    context = MagicMock()
    context.get_route_metadata.return_value = {"route": "/test"}
    return context


@pytest.fixture
def mock_comms():
    """Fixture to mock the get_comms function."""
    with patch("aikido_zen.background_process.comms.get_comms") as mock:
        yield mock


def test_ipc_lifecycle_cache_initialization(mock_context, mock_comms):
    """Test the initialization of IPCLifecycleCache."""
    # Mock the response from send_data_to_bg_process
    mock_comms().send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "bypassed_ips": {"192.168.1.1", "192.168.1.2"},
            "matched_endpoints": [{"endpoint": {"forceProtectionOff": True}}],
        },
    }

    cache = IPCLifecycleCache(mock_context)

    assert cache.bypassed_ips == {"192.168.1.1", "192.168.1.2"}
    assert cache.matched_endpoints == [{"endpoint": {"forceProtectionOff": True}}]


def test_ipc_lifecycle_cache_populate(mock_context, mock_comms):
    """Test the populate method."""
    cache = IPCLifecycleCache(mock_context)

    # Mock the response for populate
    mock_comms().send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "bypassed_ips": {"192.168.1.3"},
            "matched_endpoints": [{"endpoint": {"forceProtectionOff": False}}],
        },
    }

    cache.populate(mock_context)

    assert cache.bypassed_ips == {"192.168.1.3"}
    assert cache.matched_endpoints == [{"endpoint": {"forceProtectionOff": False}}]


def test_ipc_lifecycle_cache_is_bypassed_ip(mock_context, mock_comms):
    """Test the is_bypassed_ip method."""
    mock_comms().send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "bypassed_ips": {"192.168.1.1"},
            "matched_endpoints": [],
        },
    }

    cache = IPCLifecycleCache(mock_context)

    assert cache.is_bypassed_ip("192.168.1.1") is True
    assert cache.is_bypassed_ip("192.168.1.2") is False


def test_ipc_lifecycle_cache_protection_forced_off(mock_context, mock_comms):
    """Test the protection_forced_off method."""
    mock_comms().send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "bypassed_ips": {},
            "matched_endpoints": [{"endpoint": {"forceProtectionOff": True}}],
        },
    }

    cache = IPCLifecycleCache(mock_context)

    assert cache.protection_forced_off() is True

    # Test with forceProtectionOff set to False
    mock_comms().send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "bypassed_ips": {},
            "matched_endpoints": [{"endpoint": {"forceProtectionOff": False}}],
        },
    }

    cache.populate(mock_context)

    assert cache.protection_forced_off() is False


def test_ipc_lifecycle_cache_save(mock_context, mock_comms):
    """Test the save method."""
    cache = IPCLifecycleCache(mock_context)
    cache.save()

    assert get_cache() == cache


def test_ipc_lifecycle_cache_no_data(mock_context, mock_comms):
    """Test the behavior when no data is returned from IPC."""
    mock_comms().send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "bypassed_ips": set(),
            "matched_endpoints": [],
        },
    }

    cache = IPCLifecycleCache(mock_context)

    assert cache.bypassed_ips == set()
    assert cache.matched_endpoints == []
