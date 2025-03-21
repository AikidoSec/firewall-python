import pytest
from unittest.mock import patch, MagicMock
from aikido_zen.background_process.routes import Routes
from .thread_cache import ThreadCache, get_cache
from ..background_process.service_config import ServiceConfig
from ..context import current_context, Context
from aikido_zen.helpers.iplist import IPList


@pytest.fixture
def thread_cache():
    """Fixture to create a ThreadCache instance."""
    return ThreadCache()


class Context2(Context):
    def __init__(self):
        pass


@pytest.fixture(autouse=True)
def run_around_tests():
    Context2().set_as_current_context()
    yield
    # Make sure to reset thread cache after every test so it does not
    # interfere with other tests
    get_cache().reset()
    current_context.set(None)


def test_initialization(thread_cache: ThreadCache):
    """Test that the ThreadCache initializes correctly."""
    assert isinstance(thread_cache.routes, Routes)
    assert isinstance(thread_cache.config.bypassed_ips, IPList)
    assert thread_cache.get_endpoints() == []
    assert thread_cache.config.blocked_uids == set()
    assert thread_cache.reqs == 0


def test_is_bypassed_ip(thread_cache: ThreadCache):
    """Test checking if an IP is bypassed."""
    thread_cache.config.bypassed_ips.add("192.168.1.1")
    assert thread_cache.is_bypassed_ip("192.168.1.1") is True
    assert thread_cache.is_bypassed_ip("192.168.1.2") is False
    thread_cache.config.bypassed_ips.add("10.0.0.1/32")
    assert thread_cache.is_bypassed_ip("10.0.0.1") is True
    assert thread_cache.is_bypassed_ip("10.0.0.2.2") is False


def test_is_user_blocked(thread_cache: ThreadCache):
    """Test checking if a user ID is blocked."""
    thread_cache.config.blocked_uids.add("user123")
    assert thread_cache.is_user_blocked("user123") is True
    assert thread_cache.is_user_blocked("user456") is False


def test_reset(thread_cache: ThreadCache):
    """Test that reset empties the cache."""
    thread_cache.config.bypassed_ips.add("192.168.1.1")
    thread_cache.config.blocked_uids.add("user123")
    thread_cache.reset()

    assert isinstance(thread_cache.config.bypassed_ips, IPList)
    assert thread_cache.config.blocked_uids == set()
    assert thread_cache.reqs == 0


def test_increment_stats(thread_cache):
    """Test that incrementing stats works correctly."""
    assert thread_cache.reqs == 0
    thread_cache.increment_stats()
    assert thread_cache.reqs == 1
    thread_cache.increment_stats()
    assert thread_cache.reqs == 2


def test_renew_with_no_comms(thread_cache: ThreadCache):
    """Test that renew does not proceed if there are no communications available."""
    with patch("aikido_zen.background_process.comms.get_comms", return_value=None):
        thread_cache.renew()
        assert isinstance(thread_cache.config.bypassed_ips, IPList)
        assert thread_cache.get_endpoints() == []
        assert thread_cache.config.blocked_uids == set()
        assert thread_cache.reqs == 0


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_with_invalid_response(mock_get_comms, thread_cache: ThreadCache):
    """Test that renew handles an invalid response gracefully."""
    mock_get_comms.return_value = MagicMock()
    mock_get_comms.return_value.send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "config": "not_a_service_config",  # Invalid type
            "routes": "not_a_dict",  # Invalid type
        },
    }

    thread_cache.renew()
    assert isinstance(thread_cache.config.bypassed_ips, IPList)
    assert thread_cache.get_endpoints() == []
    assert thread_cache.config.blocked_uids == set()


def test_is_bypassed_ip_case_insensitivity(thread_cache: ThreadCache):
    """Test that IP check is case-insensitive."""
    thread_cache.config.bypassed_ips.add("192.168.1.1")
    assert thread_cache.is_bypassed_ip("192.168.1.1") is True
    assert thread_cache.is_bypassed_ip("192.168.1.1".upper()) is True


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
def test_parses_routes_correctly(
    mock_get_unixtime_ms, mock_get_comms, thread_cache: ThreadCache
):
    """Test renewing the cache multiple times if TTL has expired."""
    mock_get_comms.return_value = MagicMock()
    mock_get_comms.return_value.send_data_to_bg_process.return_value = {
        "success": True,
        "data": {
            "config": ServiceConfig(
                endpoints=[
                    {
                        "graphql": False,
                        "method": "POST",
                        "route": "/v2",
                        "rate_limiting": {
                            "enabled": False,
                        },
                        "force_protection_off": False,
                    }
                ],
                bypassed_ips=["192.168.1.1"],
                blocked_uids={"user123"},
                last_updated_at=-1,
                received_any_stats=True,
            ),
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
    thread_cache.renew()
    assert thread_cache.is_bypassed_ip("192.168.1.1")
    assert thread_cache.get_endpoints() == [
        {
            "graphql": False,
            "method": "POST",
            "route": "/v2",
            "rate_limiting": {
                "enabled": False,
            },
            "force_protection_off": False,
        }
    ]
    assert thread_cache.is_user_blocked("user123")
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
