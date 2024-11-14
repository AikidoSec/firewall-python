import pytest
from unittest.mock import patch, MagicMock
from aikido_zen.background_process.routes import Routes
from aikido_zen.background_process.comms import get_comms
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from .thread_cache import ThreadCache, THREAD_CONFIG_TTL_MS, threadlocal_storage
from ..ratelimiting.get_ratelimited_endpoint_test import endpoints
from ..storage.service_config import ServiceConfig
from ..storage.service_config_test import service_config


@pytest.fixture
def thread_cache():
    """Fixture to create a ThreadCache instance."""
    return ThreadCache()


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    # Make sure to reset thread cache after every test so it does not
    # interfere with other tests
    setattr(threadlocal_storage, "cache", None)


def test_initialization(thread_cache):
    """Test that the ThreadCache initializes correctly."""
    assert isinstance(thread_cache.routes, Routes)
    assert thread_cache.config is None
    assert thread_cache.last_renewal == -1


def test_is_bypassed_ip(thread_cache):
    """Test checking if an IP is bypassed."""
    config = ServiceConfig(
        endpoints=[],
        last_updated_at=None,
        blocked_user_ids=[],
        bypassed_ips=["192.168.1.1"],
        received_any_stats=True,
    )
    thread_cache.config = config
    assert thread_cache.is_bypassed_ip("192.168.1.1") is True
    assert thread_cache.is_bypassed_ip("192.168.1.2") is False


def test_is_user_blocked(thread_cache):
    """Test checking if a user ID is blocked."""
    config = ServiceConfig(
        endpoints=[],
        last_updated_at=None,
        blocked_user_ids=["user123"],
        bypassed_ips=["192.168.1.1"],
        received_any_stats=True,
    )
    thread_cache.config = config
    assert thread_cache.is_user_blocked("user123") is True
    assert thread_cache.is_user_blocked("user456") is False


@patch("aikido_zen.background_process.comms.get_comms")
@patch("aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms")
def test_renew_if_ttl_expired(mock_get_unixtime_ms, mock_get_comms, thread_cache):
    """Test renewing the cache if TTL has expired."""
    service_config = ServiceConfig(
        endpoints=[{"graphql": False, "route": 1}],
        last_updated_at=None,
        blocked_user_ids=["user123"],
        bypassed_ips=["192.168.1.1"],
        received_any_stats=True,
    )
    mock_get_unixtime_ms.return_value = (
        THREAD_CONFIG_TTL_MS + 1
    )  # Simulate TTL expiration
    mock_get_comms.return_value = MagicMock()
    mock_get_comms.return_value.send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "service_config": service_config,
            "routes": {},
        },
    }

    thread_cache.renew_if_ttl_expired()
    assert thread_cache.is_bypassed_ip("192.168.1.1")
    assert not thread_cache.is_bypassed_ip("192.168.0.1")
    assert thread_cache.is_user_blocked("user123") is True
    assert thread_cache.is_user_blocked("user456") is False
    assert thread_cache.config is service_config
    assert thread_cache.last_renewal > 0


@patch("aikido_zen.background_process.comms.get_comms")
@patch("aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms")
def test_renew_if_ttl_not_expired(mock_get_unixtime_ms, mock_get_comms, thread_cache):
    """Test that renew is not called if TTL has not expired."""
    mock_get_unixtime_ms.return_value = 0  # Simulate TTL not expired
    thread_cache.last_renewal = 0  # Set last renewal to 0

    thread_cache.renew_if_ttl_expired()
    assert thread_cache.last_renewal == 0  # Should not change


def test_increment_stats(thread_cache):
    """Test that incrementing stats works correctly."""
    assert thread_cache.reqs == 0
    thread_cache.increment_stats()
    assert thread_cache.reqs == 1
    thread_cache.increment_stats()
    assert thread_cache.reqs == 2


def test_renew_with_no_comms(thread_cache):
    """Test that renew does not proceed if there are no communications available."""
    with patch("aikido_zen.background_process.comms.get_comms", return_value=None):
        thread_cache.renew()
        assert thread_cache.config is None
        assert list(thread_cache.routes) == []
        assert thread_cache.reqs == 0
        assert thread_cache.last_renewal == -1


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_with_invalid_response(mock_get_comms, thread_cache):
    """Test that renew handles an invalid response gracefully."""
    service_config = ServiceConfig(
        endpoints=[{"graphql": False, "route": 1}],
        last_updated_at=None,
        blocked_user_ids=["user123"],
        bypassed_ips=["192.168.1.1"],
        received_any_stats=True,
    )
    thread_cache.config = service_config
    mock_get_comms.return_value = MagicMock()
    mock_get_comms.return_value.send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "service_config": "not_a_service_config",  # Invalid type
            "routes": {
                "POST:/body": {
                    "method": "POST",
                    "path": "/body",
                    "hits": 20,
                    "hits_delta_since_sync": 25,
                    "apispec": {},
                },
                "GET:/body": {
                    "method": "GET",
                    "path": "/body",
                    "hits": 10,
                    "hits_delta_since_sync": 5,
                    "apispec": {},
                },
            },
        },
    }

    thread_cache.renew()
    assert thread_cache.config == service_config  # Remains unchanged
    assert list(thread_cache.routes) == [
        {
            "method": "POST",
            "path": "/body",
            "hits": 20,
            "hits_delta_since_sync": 0,
            "apispec": {},
        },
        {
            "method": "GET",
            "path": "/body",
            "hits": 10,
            "hits_delta_since_sync": 0,
            "apispec": {},
        },
    ]
    assert thread_cache.last_renewal > 0  # Should update last_renewal


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_with_invalid_response_routes(mock_get_comms, thread_cache):
    """Test that renew handles an invalid response gracefully."""
    service_config = ServiceConfig(
        endpoints=[{"graphql": False, "route": 1}],
        last_updated_at=None,
        blocked_user_ids=["user123"],
        bypassed_ips=["192.168.1.1"],
        received_any_stats=True,
    )
    thread_cache.config = service_config
    mock_get_comms.return_value = MagicMock()
    mock_get_comms.return_value.send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "service_config": "not_a_service_config",  # Invalid type
            "routes": "not_routes",
        },
    }

    thread_cache.renew()
    assert thread_cache.config == service_config  # Remains unchanged
    assert list(thread_cache.routes) == []
    assert thread_cache.last_renewal > 0  # Should update last_renewal


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_not_success(mock_get_comms, thread_cache):
    """Test that renew handles an invalid response gracefully."""
    service_config = ServiceConfig(
        endpoints=[{"graphql": False, "route": 1}],
        last_updated_at=None,
        blocked_user_ids=["user123"],
        bypassed_ips=["192.168.1.1"],
        received_any_stats=True,
    )
    thread_cache.config = service_config
    mock_get_comms.return_value = MagicMock()
    mock_get_comms.return_value.send_data_to_bg_process.return_value = {
        "success": False,
    }

    thread_cache.renew()
    assert thread_cache.config == service_config  # Remains unchanged
    assert list(thread_cache.routes) == []  # Remains unchanged
    assert thread_cache.last_renewal == -1


def test_increment_stats_thread_safety(thread_cache):
    """Test that incrementing stats is thread-safe."""
    from threading import Thread

    def increment_in_thread():
        for _ in range(100):
            thread_cache.increment_stats()

    threads = [Thread(target=increment_in_thread) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert thread_cache.reqs == 1000  # 10 threads incrementing 100 times


@patch("aikido_zen.background_process.comms.get_comms")
@patch("aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms")
def test_renew_if_ttl_expired_multiple_times(
    mock_get_unixtime_ms, mock_get_comms, thread_cache
):
    """Test renewing the cache multiple times if TTL has expired."""
    service_config = ServiceConfig(
        endpoints=[{"graphql": False, "route": 1}],
        last_updated_at=None,
        blocked_user_ids=["user123"],
        bypassed_ips=["192.168.1.1"],
        received_any_stats=True,
    )
    mock_get_unixtime_ms.return_value = (
        THREAD_CONFIG_TTL_MS + 1
    )  # Simulate TTL expiration
    mock_get_comms.return_value = MagicMock()
    mock_get_comms.return_value.send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "service_config": service_config,
            "routes": {},
        },
    }

    # First renewal
    thread_cache.renew_if_ttl_expired()
    assert thread_cache.config.endpoints == [{"graphql": False, "route": 1}]
    assert thread_cache.is_bypassed_ip("192.168.1.1")
    assert not thread_cache.is_bypassed_ip("192.168.0.1")
    assert thread_cache.is_user_blocked("user123") is True
    assert thread_cache.is_user_blocked("user456") is False

    # Simulate another TTL expiration
    mock_get_unixtime_ms.return_value += THREAD_CONFIG_TTL_MS + 1
    thread_cache.renew_if_ttl_expired()
    assert thread_cache.config.endpoints == [{"graphql": False, "route": 1}]
    assert thread_cache.is_bypassed_ip("192.168.1.1")
    assert not thread_cache.is_bypassed_ip("192.168.0.1")
    assert thread_cache.is_user_blocked("user123") is True
    assert thread_cache.is_user_blocked("user456") is False


@patch("aikido_zen.background_process.comms.get_comms")
@patch("aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms")
def test_parses_routes_correctly(mock_get_unixtime_ms, mock_get_comms, thread_cache):
    """Test renewing the cache multiple times if TTL has expired."""
    service_config = ServiceConfig(
        endpoints=[{"graphql": False, "route": 1}],
        last_updated_at=None,
        blocked_user_ids=["user123"],
        bypassed_ips=["192.168.1.1"],
        received_any_stats=True,
    )
    mock_get_unixtime_ms.return_value = (
        THREAD_CONFIG_TTL_MS + 1
    )  # Simulate TTL expiration
    mock_get_comms.return_value = MagicMock()
    mock_get_comms.return_value.send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "service_config": service_config,
            "routes": {
                "POST:/body": {
                    "method": "POST",
                    "path": "/body",
                    "hits": 20,
                    "hits_delta_since_sync": 25,
                    "apispec": {},
                },
                "GET:/body": {
                    "method": "GET",
                    "path": "/body",
                    "hits": 10,
                    "hits_delta_since_sync": 5,
                    "apispec": {},
                },
            },
        },
    }

    # First renewal
    thread_cache.renew_if_ttl_expired()
    assert thread_cache.config.endpoints == [{"graphql": False, "route": 1}]
    assert thread_cache.is_bypassed_ip("192.168.1.1")
    assert not thread_cache.is_bypassed_ip("192.168.0.1")
    assert thread_cache.is_user_blocked("user123") is True
    assert thread_cache.is_user_blocked("user456") is False
    assert list(thread_cache.routes) == [
        {
            "method": "POST",
            "path": "/body",
            "hits": 20,
            "hits_delta_since_sync": 0,
            "apispec": {},
        },
        {
            "method": "GET",
            "path": "/body",
            "hits": 10,
            "hits_delta_since_sync": 0,
            "apispec": {},
        },
    ]
