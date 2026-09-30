from copy import deepcopy
from unittest.mock import MagicMock

import pytest

from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from aikido_zen.background_process.commands.sync_data import process_sync_data
from aikido_zen.context import Context, current_context
from aikido_zen.sources.functions.request_handler import post_response
from aikido_zen.thread.thread_cache import ThreadCache


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
