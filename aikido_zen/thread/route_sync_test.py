from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from aikido_zen.background_process.commands.sync_data import process_sync_data
from aikido_zen.context import Context, current_context
from aikido_zen.sources.functions.request_handler import post_response
from aikido_zen.thread.thread_cache import ThreadCache


@pytest.fixture(params=[False, True])
def sync(request):
    cache = ThreadCache()
    manager = CloudConnectionManager(False, MagicMock(), "test-token", None)
    manager.conf.last_updated_at = 1 if request.param else -1
    manager.report_api_event = MagicMock(return_value={"success": False})
    context = Context(body={"name": "example"})
    context.route, context.method, context.remote_address = "/test", "POST", "1.2.3.4"
    token = current_context.set(context)
    comms = MagicMock()
    comms.send_data_to_bg_process.side_effect = lambda action, obj, receive: {
        "success": True,
        "data": deepcopy(process_sync_data(manager, deepcopy(obj))),
    }
    with (
        patch("aikido_zen.background_process.comms.get_comms", return_value=comms),
        patch(
            "aikido_zen.sources.functions.request_handler.get_cache", return_value=cache
        ),
        patch(
            "aikido_zen.sources.functions.request_handler.get_api_info",
            wraps=get_api_info,
        ) as generate_schema,
    ):
        yield cache, manager, comms, generate_schema, context
    current_context.reset(token)


@pytest.mark.parametrize("first_sync_fails", [False, True])
@pytest.mark.parametrize("concurrent_path", [None, "/test", "/new"])
def test_sync_counts_each_request_once(sync, first_sync_fails, concurrent_path):
    cache, manager, comms, _, context = sync
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
    sent_routes = [
        call.kwargs["obj"]["current_routes"]
        for call in comms.send_data_to_bg_process.call_args_list
    ]
    assert [
        sum(route["hits_delta_since_sync"] for route in batch.values())
        for batch in sent_routes
    ] == [1, int(concurrent_path is not None), 0]
    if concurrent_path:
        route = manager.routes.get({"method": "POST", "route": concurrent_path})
        assert "during" in route["apispec"]["body"]["schema"]["properties"]


@pytest.mark.parametrize("sync_fails", [False, True])
@pytest.mark.parametrize("requests_per_sync, expected_samples", [(1, 1200), (30, 80)])
def test_sampling_resets_every_ten_syncs(
    sync, sync_fails, requests_per_sync, expected_samples
):
    cache, manager, comms, generate_schema, _ = sync
    if sync_fails:
        comms.send_data_to_bg_process.side_effect = None
        comms.send_data_to_bg_process.return_value = {"success": False}

    for request in range(1200):
        post_response(200)
        if (request + 1) % requests_per_sync == 0:
            cache.renew()

    assert generate_schema.call_count == expected_samples
    if not sync_fails:
        route = manager.routes.get({"method": "POST", "route": "/test"})
        assert route["hits"] == 1200
        assert route["apispec"]["body"]["schema"]["properties"] == {
            "name": {"type": "string"}
        }


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


def test_sampling_reset_preserves_requests_during_sync(sync):
    cache, _, comms, generate_schema, _ = sync
    for _ in range(30):
        post_response(200)
    for _ in range(9):
        cache.renew()
    assert generate_schema.call_count == 20
    deliver = comms.send_data_to_bg_process.side_effect

    def sample_during_sync(action, obj, receive):
        post_response(200)
        return deliver(action, obj, receive)

    comms.send_data_to_bg_process.side_effect = sample_during_sync
    cache.renew()
    assert generate_schema.call_count == 21
    for _ in range(30):
        post_response(200)
    assert generate_schema.call_count == 40
