import pytest
from unittest.mock import MagicMock, patch
import aikido_zen.test_utils as test_utils

from aikido_zen.background_process.routes import Routes
from . import process_worker_loader
from .thread_cache import ThreadCache, get_cache
from .. import set_user
from ..background_process.packages import PackagesStore
from ..background_process.service_config import ServiceConfig
from ..context import current_context
from aikido_zen.helpers.ip_matcher import IPMatcher


@pytest.fixture
def thread_cache():
    """Fixture to create a ThreadCache instance."""
    with test_utils.patch_time(time_ms=-1):
        return ThreadCache()


@pytest.fixture(autouse=True)
def run_around_tests():
    test_utils.generate_and_set_context()
    yield
    # Make sure to reset thread cache after every test so it does not
    # interfere with other tests
    get_cache().reset()
    current_context.set(None)


def test_initialization(thread_cache: ThreadCache):
    """Test that the ThreadCache initializes correctly."""
    assert isinstance(thread_cache.routes, Routes)
    assert isinstance(thread_cache.config.bypassed_ips, IPMatcher)
    assert thread_cache.get_endpoints() == []
    assert thread_cache.config.blocked_uids == set()
    assert thread_cache.stats.get_record()["requests"] == {
        "total": 0,
        "rateLimited": 0,
        "aborted": 0,
        "attacksDetected": {"total": 0, "blocked": 0},
        "attackWaves": {"total": 0, "blocked": 0},
    }


def test_is_bypassed_ip(thread_cache: ThreadCache):
    """Test checking if an IP is bypassed."""
    thread_cache.config.bypassed_ips = IPMatcher(["192.168.1.1"])
    assert thread_cache.is_bypassed_ip("192.168.1.1") is True
    assert thread_cache.is_bypassed_ip("192.168.1.2") is False
    thread_cache.config.bypassed_ips = IPMatcher(["192.168.1.1", "10.0.0.1/32"])
    assert thread_cache.is_bypassed_ip("10.0.0.1") is True
    assert thread_cache.is_bypassed_ip("10.0.0.2.2") is False


def test_is_user_blocked(thread_cache: ThreadCache):
    """Test checking if a user ID is blocked."""
    thread_cache.config.blocked_uids.add("user123")
    assert thread_cache.is_user_blocked("user123") is True
    assert thread_cache.is_user_blocked("user456") is False


def test_reset(thread_cache: ThreadCache):
    """Test that reset empties the cache."""
    thread_cache.config.bypassed_ips = IPMatcher(["192.168.1.1"])
    thread_cache.config.blocked_uids.add("user123")
    thread_cache.stats.increment_total_hits()
    thread_cache.stats.on_detected_attack(blocked=True, operation="test")

    thread_cache.reset()

    assert isinstance(thread_cache.config.bypassed_ips, IPMatcher)
    assert thread_cache.config.blocked_uids == set()
    assert thread_cache.stats.get_record()["requests"] == {
        "total": 0,
        "rateLimited": 0,
        "aborted": 0,
        "attacksDetected": {"total": 0, "blocked": 0},
        "attackWaves": {"total": 0, "blocked": 0},
    }


def test_increment_total_hits(thread_cache):
    """Test that incrementing stats works correctly."""
    assert thread_cache.stats.get_record()["requests"]["total"] == 0
    thread_cache.stats.increment_total_hits()
    assert thread_cache.stats.get_record()["requests"]["total"] == 1
    thread_cache.stats.increment_total_hits()
    assert thread_cache.stats.get_record()["requests"]["total"] == 2


def test_renew_with_no_comms(thread_cache: ThreadCache):
    """Test that renew does not proceed if there are no communications available."""
    with patch("aikido_zen.background_process.comms.get_comms", return_value=None):
        thread_cache.renew()
        assert isinstance(thread_cache.config.bypassed_ips, IPMatcher)
        assert thread_cache.get_endpoints() == []
        assert thread_cache.config.blocked_uids == set()
        assert thread_cache.stats.get_record()["requests"] == {
            "total": 0,
            "rateLimited": 0,
            "aborted": 0,
            "attacksDetected": {"total": 0, "blocked": 0},
            "attackWaves": {"total": 0, "blocked": 0},
        }


@patch.object(process_worker_loader.thread_cache, "renew")
@patch.object(
    process_worker_loader.thread_cache, "is_config_loaded", return_value=False
)
@patch.object(process_worker_loader.threading, "Thread")
@patch.object(process_worker_loader.threading, "enumerate", return_value=[])
@patch.object(process_worker_loader, "get_current_context", return_value=object())
def test_load_worker_renews_cache_before_starting_thread(
    _mock_context,
    _mock_enumerate,
    mock_thread_type,
    _mock_is_config_loaded,
    mock_renew,
):
    call_order = []
    thread = mock_thread_type.return_value
    thread.start.side_effect = lambda: call_order.append("start")
    mock_renew.side_effect = lambda: call_order.append("renew")

    process_worker_loader.load_worker()

    assert call_order == ["renew", "start"]
    assert thread.daemon is True


@patch.object(process_worker_loader.thread_cache, "renew")
@patch.object(process_worker_loader.thread_cache, "is_config_loaded", return_value=True)
@patch.object(process_worker_loader.threading, "Thread")
@patch.object(process_worker_loader.threading, "enumerate")
@patch.object(process_worker_loader, "get_current_context", return_value=object())
def test_load_worker_does_not_initialize_when_worker_is_running(
    _mock_context,
    mock_enumerate,
    mock_thread_type,
    _mock_is_config_loaded,
    mock_renew,
):
    worker = MagicMock()
    worker.name = "aikido-process-worker-" + str(
        process_worker_loader.multiprocessing.current_process().pid
    )
    mock_enumerate.return_value = [worker]

    process_worker_loader.load_worker()

    mock_renew.assert_not_called()
    mock_thread_type.assert_not_called()


@patch.object(process_worker_loader.thread_cache, "renew")
@patch.object(
    process_worker_loader.thread_cache, "is_config_loaded", return_value=False
)
@patch.object(process_worker_loader.threading, "Thread")
@patch.object(process_worker_loader.threading, "enumerate")
@patch.object(process_worker_loader, "get_current_context", return_value=object())
def test_load_worker_retries_cache_initialization_when_worker_is_running(
    _mock_context,
    mock_enumerate,
    mock_thread_type,
    _mock_is_config_loaded,
    mock_renew,
):
    worker = MagicMock()
    worker.name = "aikido-process-worker-" + str(
        process_worker_loader.multiprocessing.current_process().pid
    )
    mock_enumerate.return_value = [worker]

    process_worker_loader.load_worker()

    mock_renew.assert_called_once_with()
    mock_thread_type.assert_not_called()


@patch.object(process_worker_loader.logger, "warning")
@patch.object(process_worker_loader.thread_cache, "renew")
@patch.object(
    process_worker_loader.thread_cache, "is_config_loaded", return_value=False
)
@patch.object(process_worker_loader.threading, "Thread")
@patch.object(process_worker_loader.threading, "enumerate", return_value=[])
@patch.object(process_worker_loader, "get_current_context", return_value=object())
def test_load_worker_starts_thread_when_cache_renewal_fails(
    _mock_context,
    _mock_enumerate,
    mock_thread_type,
    _mock_is_config_loaded,
    mock_renew,
    mock_warning,
):
    error = RuntimeError("sync failed")
    mock_renew.side_effect = error

    process_worker_loader.load_worker()

    mock_thread_type.return_value.start.assert_called_once_with()
    mock_warning.assert_called_once_with(
        "An error occurred during data synchronization: %s", error
    )


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
    assert isinstance(thread_cache.config.bypassed_ips, IPMatcher)
    assert thread_cache.get_endpoints() == []
    assert thread_cache.config.blocked_uids == set()


def test_is_bypassed_ip_case_insensitivity(thread_cache: ThreadCache):
    """Test that IP check is case-insensitive."""
    thread_cache.config.bypassed_ips = IPMatcher(["192.168.1.1"])
    assert thread_cache.is_bypassed_ip("192.168.1.1") is True
    assert thread_cache.is_bypassed_ip("192.168.1.1".upper()) is True


def test_increment_stats_thread_safety(thread_cache):
    """Test that incrementing stats is thread-safe."""
    from threading import Thread

    def increment_in_thread():
        for _ in range(100):
            thread_cache.stats.increment_total_hits()

    threads = [Thread(target=increment_in_thread) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert (
        thread_cache.stats.get_record()["requests"]["total"] == 1000
    )  # 10 threads incrementing 100 times


@patch("aikido_zen.background_process.comms.get_comms")
def test_parses_routes_correctly(mock_get_comms, thread_cache: ThreadCache):
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


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_called_with_correct_args(mock_get_comms, thread_cache: ThreadCache):
    """Test that renew calls send_data_to_bg_process with correct arguments."""
    mock_comms = MagicMock()
    mock_get_comms.return_value = mock_comms

    # Setup initial state
    thread_cache.stats.increment_total_hits()
    thread_cache.stats.increment_total_hits()
    thread_cache.stats.operations.register_call("op1", "sql_op")
    thread_cache.stats.operations.register_call("op2", "sql_op")
    thread_cache.stats.on_detected_attack(blocked=True, operation="op1")
    thread_cache.stats.on_detected_attack(blocked=False, operation="op1")
    thread_cache.stats.on_detected_attack(blocked=False, operation="op2")
    thread_cache.routes.initialize_route({"method": "GET", "route": "/test"})
    thread_cache.routes.increment_route({"method": "GET", "route": "/test"})
    thread_cache.ai_stats.on_ai_call("openai", "gpt-4o", 6427, 200)
    thread_cache.ai_stats.on_ai_call("openai", "gpt-4o2", 424, 235)
    thread_cache.ai_stats.on_ai_call("openai", "gpt-4o2", 232, 932)
    thread_cache.ai_stats.on_ai_call("openai", "gpt-4o3", 8223, 173)

    # Call renew
    with test_utils.patch_time(time_ms=-1):
        PackagesStore.add_package("test-package-4", "4.3.0")
        PackagesStore.clear()
        PackagesStore.add_package("test-package-1", "4.3.0")
        thread_cache.renew()

    assert thread_cache.ai_stats.empty()
    assert PackagesStore.get_package("test-package-1") == {
        "cleared": True,
        "name": "test-package-1",
        "requiredAt": -1,
        "version": "4.3.0",
    }
    assert PackagesStore.export() == []

    # Assert that send_data_to_bg_process was called with the correct arguments
    mock_comms.send_data_to_bg_process.assert_called_once_with(
        action="SYNC_DATA",
        obj={
            "current_routes": {
                "GET:/test": {
                    "method": "GET",
                    "path": "/test",
                    "hits": 1,
                    "hits_delta_since_sync": 1,
                    "apispec": {},
                }
            },
            "stats": {
                "startedAt": -1,
                "endedAt": -1,
                "requests": {
                    "total": 2,
                    "rateLimited": 0,
                    "aborted": 0,
                    "attacksDetected": {"blocked": 1, "total": 3},
                    "attackWaves": {"total": 0, "blocked": 0},
                },
                "operations": {
                    "op1": {
                        "attacksDetected": {"blocked": 1, "total": 2},
                        "kind": "sql_op",
                        "total": 1,
                    },
                    "op2": {
                        "attacksDetected": {"blocked": 0, "total": 1},
                        "kind": "sql_op",
                        "total": 1,
                    },
                },
            },
            "ai_stats": [
                {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "calls": 1,
                    "tokens": {"input": 6427, "output": 200, "total": 6627},
                },
                {
                    "provider": "openai",
                    "model": "gpt-4o2",
                    "calls": 2,
                    "tokens": {"input": 656, "output": 1167, "total": 1823},
                },
                {
                    "provider": "openai",
                    "model": "gpt-4o3",
                    "calls": 1,
                    "tokens": {"input": 8223, "output": 173, "total": 8396},
                },
            ],
            "middleware_installed": False,
            "hostnames": [],
            "users": [],
            "packages": [
                {
                    "name": "test-package-1",
                    "version": "4.3.0",
                    "requiredAt": -1,
                    "cleared": False,
                }
            ],
        },
        receive=True,
    )


@patch("aikido_zen.background_process.comms.get_comms")
def test_sync_data_for_users(mock_get_comms, thread_cache: ThreadCache):
    """Test that renew calls send_data_to_bg_process with correct arguments."""
    mock_comms = MagicMock()
    mock_get_comms.return_value = mock_comms
    test_utils.generate_and_set_context(ip="5.6.7.8")

    # Setup initial state
    thread_cache.stats.increment_total_hits()
    with patch("aikido_zen.thread.thread_cache.get_cache", return_value=thread_cache):
        with test_utils.patch_time(time_ms=1):
            set_user({"id": "123", "name": "test"})
            set_user({"id": "567", "name": "test"})

    with test_utils.patch_time(time_ms=-1):
        thread_cache.renew()

    # Assert that send_data_to_bg_process was called with the correct arguments
    mock_comms.send_data_to_bg_process.assert_called_once_with(
        action="SYNC_DATA",
        obj={
            "current_routes": {},
            "stats": {
                "startedAt": -1,
                "endedAt": -1,
                "requests": {
                    "total": 1,
                    "rateLimited": 0,
                    "aborted": 0,
                    "attacksDetected": {"total": 0, "blocked": 0},
                    "attackWaves": {"total": 0, "blocked": 0},
                },
                "operations": {},
            },
            "middleware_installed": False,
            "hostnames": [],
            "ai_stats": [],
            "packages": [],
            "users": [
                {
                    "id": "123",
                    "name": "test",
                    "lastIpAddress": "5.6.7.8",
                    "firstSeenAt": 1,
                    "lastSeenAt": 1,
                },
                {
                    "id": "567",
                    "name": "test",
                    "lastIpAddress": "5.6.7.8",
                    "firstSeenAt": 1,
                    "lastSeenAt": 1,
                },
            ],
        },
        receive=True,
    )


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_called_with_empty_routes(mock_get_comms, thread_cache: ThreadCache):
    """Test that renew calls send_data_to_bg_process with empty routes."""
    mock_comms = MagicMock()
    mock_get_comms.return_value = mock_comms

    with test_utils.patch_time(time_ms=-1):
        thread_cache.renew()

    # Assert that send_data_to_bg_process was called with the correct arguments
    mock_comms.send_data_to_bg_process.assert_called_once_with(
        action="SYNC_DATA",
        obj={
            "current_routes": {},
            "stats": {
                "startedAt": -1,
                "endedAt": -1,
                "requests": {
                    "total": 0,
                    "rateLimited": 0,
                    "aborted": 0,
                    "attacksDetected": {"total": 0, "blocked": 0},
                    "attackWaves": {"total": 0, "blocked": 0},
                },
                "operations": {},
            },
            "middleware_installed": False,
            "hostnames": [],
            "users": [],
            "ai_stats": [],
            "packages": [],
        },
        receive=True,
    )


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_preserves_increments_during_ipc(
    mock_get_comms, thread_cache: ThreadCache
):
    """Increments arriving during the IPC call survive on the response path -
    the snapshot is sent, but the live counter keeps the concurrent increment."""
    mock_comms = MagicMock()
    mock_get_comms.return_value = mock_comms

    thread_cache.stats.increment_total_hits()
    thread_cache.stats.increment_total_hits()

    def simulate_concurrent_increment(*args, **kwargs):
        thread_cache.stats.increment_total_hits()
        return {"success": True, "data": {"routes": {}}}

    mock_comms.send_data_to_bg_process.side_effect = simulate_concurrent_increment

    thread_cache.renew()

    sent_total = mock_comms.send_data_to_bg_process.call_args.kwargs["obj"]["stats"][
        "requests"
    ]["total"]
    assert sent_total == 2
    assert thread_cache.stats.get_record()["requests"]["total"] == 1


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_restores_deltas_on_ipc_failure(
    mock_get_comms, thread_cache: ThreadCache
):
    """If the IPC fails, the cleared deltas must be merged back on top of any
    concurrent increments - nothing lost, nothing double-counted."""
    mock_comms = MagicMock()
    mock_get_comms.return_value = mock_comms

    thread_cache.stats.increment_total_hits()
    thread_cache.stats.increment_total_hits()
    thread_cache.ai_stats.on_ai_call("openai", "gpt-4o", 100, 50)
    thread_cache.middleware_installed = True

    def fail_after_concurrent_increment(*args, **kwargs):
        thread_cache.stats.increment_total_hits()
        return {"success": False}

    mock_comms.send_data_to_bg_process.side_effect = fail_after_concurrent_increment

    thread_cache.renew()

    # 2 from the snapshot + 1 from the concurrent increment
    assert thread_cache.stats.get_record()["requests"]["total"] == 3
    assert thread_cache.middleware_installed is True
    assert thread_cache.ai_stats.get_stats()[0]["calls"] == 1


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_called_with_no_requests(mock_get_comms, thread_cache: ThreadCache):
    """Test that renew calls send_data_to_bg_process with zero requests."""
    mock_comms = MagicMock()
    mock_get_comms.return_value = mock_comms

    # Setup initial state with a route but no requests
    thread_cache.routes.initialize_route({"method": "GET", "route": "/test"})

    with test_utils.patch_time(time_ms=-1):
        thread_cache.renew()

    # Assert that send_data_to_bg_process was called with the correct arguments
    mock_comms.send_data_to_bg_process.assert_called_once_with(
        action="SYNC_DATA",
        obj={
            "current_routes": {},
            "stats": {
                "startedAt": -1,
                "endedAt": -1,
                "requests": {
                    "total": 0,
                    "rateLimited": 0,
                    "aborted": 0,
                    "attacksDetected": {"total": 0, "blocked": 0},
                    "attackWaves": {"total": 0, "blocked": 0},
                },
                "operations": {},
            },
            "middleware_installed": False,
            "hostnames": [],
            "users": [],
            "ai_stats": [],
            "packages": [],
        },
        receive=True,
    )
