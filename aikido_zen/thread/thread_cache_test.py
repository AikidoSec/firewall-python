from copy import deepcopy

import pytest
from unittest.mock import MagicMock, patch
import aikido_zen.test_utils as test_utils

from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from aikido_zen.background_process.commands.sync_data import process_sync_data
from aikido_zen.background_process.routes import Routes
from aikido_zen.sources.functions.request_handler import post_response
from . import process_worker_loader
from .thread_cache import ThreadCache, get_cache
from .. import set_user
from ..background_process.packages import PackagesStore
from ..background_process.service_config import ServiceConfig
from ..context import Context, current_context
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


@pytest.fixture
def sync(monkeypatch):
    cache = ThreadCache()
    manager = CloudConnectionManager(False, MagicMock(), "test-token", None)
    manager.conf.last_updated_at = 1
    manager.report_api_event = MagicMock(return_value={"success": False})
    context = Context(body={"name": "example"})
    context.route, context.method, context.remote_address = "/test", "POST", "1.2.3.4"
    token = current_context.set(context)
    comms = MagicMock()
    comms.send_data_to_bg_process.side_effect = lambda action, obj, receive: {
        "success": True,
        "data": deepcopy(process_sync_data(manager, deepcopy(obj))),
    }
    generate_schema = MagicMock(wraps=get_api_info)
    monkeypatch.setattr("aikido_zen.background_process.comms.get_comms", lambda: comms)
    monkeypatch.setattr(
        "aikido_zen.sources.functions.request_handler.get_cache", lambda: cache
    )
    monkeypatch.setattr(
        "aikido_zen.sources.functions.request_handler.get_api_info", generate_schema
    )
    yield cache, manager, comms, generate_schema, context
    current_context.reset(token)


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
def test_renew_updates_config(mock_get_comms, thread_cache: ThreadCache):
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


@pytest.mark.parametrize("config_loaded", [False, True])
@pytest.mark.parametrize("first_sync_fails", [False, True])
@pytest.mark.parametrize("concurrent_path", [None, "/test", "/new"])
def test_sync_counts_each_request_once(
    sync, config_loaded, first_sync_fails, concurrent_path
):
    cache, manager, comms, _, context = sync
    manager.conf.last_updated_at = 1 if config_loaded else -1
    deliver = comms.send_data_to_bg_process.side_effect
    cache.stats.increment_total_hits()
    post_response(200)

    def first_sync(action, obj, receive):
        response = (
            {"success": False} if first_sync_fails else deliver(action, obj, receive)
        )
        if concurrent_path:
            context.route, context.body = concurrent_path, {"during": "sync"}
            cache.stats.increment_total_hits()
            post_response(200)
        return response

    comms.send_data_to_bg_process.side_effect = first_sync
    cache.renew()
    comms.send_data_to_bg_process.side_effect = deliver
    cache.renew()
    cache.renew()

    expected = int(not first_sync_fails) + int(concurrent_path is not None)
    assert sum(route["hits"] for route in manager.routes) == expected
    assert manager.statistics.get_record()["requests"]["total"] == expected
    assert cache.routes.get_routes_with_hits() == {}
    if concurrent_path:
        route = manager.routes.get({"method": "POST", "route": concurrent_path})
        assert "during" in route["apispec"]["body"]["schema"]["properties"]


def test_sync_merges_optional_fields_without_reusing_previous_heartbeat_schema(sync):
    cache, manager, _, _, context = sync
    for optional_property in ("first", "second"):
        for body in (
            {"always": "value", optional_property: "value"},
            {"always": "value"},
        ):
            context.body = body
            post_response(200)
            cache.renew()

        manager.send_heartbeat()
        report = manager.report_api_event.call_args.args[0]
        assert len(report["routes"]) == 1
        assert report["routes"][0]["hits"] == 2
        assert report["routes"][0]["apispec"]["body"]["schema"]["properties"] == {
            "always": {"type": "string"},
            optional_property: {"type": "string", "optional": True},
        }


def test_overlapping_syncs_do_not_replay_hits(sync):
    cache, manager, comms, _, _ = sync
    deliver = comms.send_data_to_bg_process.side_effect
    post_response(200)

    def first_sync(action, obj, receive):
        comms.send_data_to_bg_process.side_effect = deliver
        post_response(200)
        cache.renew()
        return deliver(action, obj, receive)

    comms.send_data_to_bg_process.side_effect = first_sync
    cache.renew()
    assert manager.routes.get({"method": "POST", "route": "/test"})["hits"] == 2
    assert cache.routes.get_routes_with_hits() == {}


@pytest.mark.parametrize("sync_fails", [False, True])
@pytest.mark.parametrize("initial_requests, samples_before_reset", [(1, 10), (21, 20)])
def test_sampling_limit_resets_during_tenth_sync(
    sync, sync_fails, initial_requests, samples_before_reset
):
    cache, manager, comms, generate_schema, _ = sync
    manager.conf.last_updated_at = -1
    if sync_fails:
        comms.send_data_to_bg_process.side_effect = lambda action, obj, receive: {
            "success": False
        }
    for _ in range(initial_requests):
        post_response(200)
    for _ in range(9):
        cache.renew()
        post_response(200)
    assert generate_schema.call_count == samples_before_reset
    deliver = comms.send_data_to_bg_process.side_effect

    def sample_during_sync(action, obj, receive):
        post_response(200)
        return deliver(action, obj, receive)

    comms.send_data_to_bg_process.side_effect = sample_during_sync
    cache.renew()
    assert generate_schema.call_count == samples_before_reset + 1
    for _ in range(20):
        post_response(200)
    assert generate_schema.call_count == samples_before_reset + 20
    comms.send_data_to_bg_process.side_effect = deliver
    cache.renew()
    if not sync_fails:
        route = manager.routes.get({"method": "POST", "route": "/test"})
        assert route["hits"] == initial_requests + 30
        assert route["apispec"]["body"]["schema"]["properties"] == {
            "name": {"type": "string"}
        }


@pytest.mark.parametrize("response_data", [{}, {"config": None}])
@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_preserves_increments_during_ipc(
    mock_get_comms, thread_cache: ThreadCache, response_data
):
    """Increments arriving during the IPC call survive on the response path -
    the snapshot is sent, but the live counter keeps the concurrent increment."""
    mock_comms = MagicMock()
    mock_get_comms.return_value = mock_comms

    thread_cache.stats.increment_total_hits()
    thread_cache.stats.increment_total_hits()

    def simulate_concurrent_increment(*args, **kwargs):
        thread_cache.stats.increment_total_hits()
        return {"success": True, "data": response_data}

    mock_comms.send_data_to_bg_process.side_effect = simulate_concurrent_increment

    thread_cache.renew()

    sent_total = mock_comms.send_data_to_bg_process.call_args.kwargs["obj"]["stats"][
        "requests"
    ]["total"]
    assert sent_total == 2
    assert thread_cache.stats.get_record()["requests"]["total"] == 1


@patch("aikido_zen.background_process.comms.get_comms")
def test_renew_drops_failed_batch_and_preserves_new_increments(
    mock_get_comms, thread_cache: ThreadCache
):
    mock_comms = MagicMock()
    mock_get_comms.return_value = mock_comms

    thread_cache.stats.increment_total_hits()
    thread_cache.stats.increment_total_hits()
    thread_cache.stats.on_detected_attack_wave(blocked=True)
    thread_cache.ai_stats.on_ai_call("openai", "gpt-4o", 100, 50)
    thread_cache.middleware_installed = True

    def fail_after_concurrent_increment(*args, **kwargs):
        thread_cache.stats.increment_total_hits()
        thread_cache.stats.on_detected_attack_wave(blocked=False)
        return {"success": False}

    mock_comms.send_data_to_bg_process.side_effect = fail_after_concurrent_increment

    thread_cache.renew()

    assert thread_cache.stats.get_record()["requests"]["total"] == 1
    assert thread_cache.stats.get_record()["requests"]["attackWaves"] == {
        "total": 1,
        "blocked": 0,
    }
    assert thread_cache.middleware_installed is False
    assert thread_cache.ai_stats.get_stats() == []


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
