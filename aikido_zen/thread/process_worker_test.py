import socket
import threading
from multiprocessing.connection import Connection
from unittest.mock import MagicMock, patch

import pytest

from aikido_zen.api_discovery.get_data_schema import get_data_schema
from aikido_zen.background_process.ipc import IPCClient
from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from aikido_zen.background_process.commands import sync_data
from aikido_zen.background_process.routes import Routes
import aikido_zen.thread.process_worker as process_worker
import aikido_zen.thread.thread_cache as thread_cache


def sleeps_over(iterations, config_loaded=False, clock_step=0):
    """Runs the worker loop and returns the sleep it chose on each pass"""
    slept = []

    def stop_eventually(seconds):
        slept.append(seconds)
        if len(slept) >= iterations:
            raise KeyboardInterrupt

    thread_cache.global_thread_cache.reset()
    if config_loaded:
        thread_cache.global_thread_cache.config.last_updated_at = 1

    clock = [0.0]

    def fake_monotonic():
        clock[0] += clock_step
        return clock[0]

    with patch("aikido_zen.thread.thread_cache.renew"), patch(
        "time.monotonic", side_effect=fake_monotonic
    ), patch("time.sleep", side_effect=stop_eventually):
        try:
            process_worker.aikido_process_worker_thread()
        except KeyboardInterrupt:
            pass
    return slept


def test_retries_quickly_while_waiting_for_the_first_config():
    assert sleeps_over(3) == [process_worker.INITIAL_CONFIG_RETRY_SECONDS] * 3


def test_uses_the_normal_interval_once_the_config_arrived():
    assert (
        sleeps_over(2, config_loaded=True)
        == [process_worker.RENEW_CACHE_EVERY_X_SEC] * 2
    )


def test_stops_retrying_quickly_when_the_config_never_arrives():
    sleeps = sleeps_over(
        2, clock_step=process_worker.INITIAL_CONFIG_RETRY_WINDOW_SECONDS
    )

    assert sleeps == [process_worker.RENEW_CACHE_EVERY_X_SEC] * 2


def test_periodic_sync_delivers_large_batch_after_receiver_stall(monkeypatch):
    cache = thread_cache.ThreadCache()
    for index in range(1000):
        metadata = {"method": "POST", "route": f"/api/resource/{index}/update"}
        cache.routes.increment_route(metadata)
        cache.stats.increment_total_hits()
        body = {f"property_{field:03d}": "value" for field in range(50)}
        cache.routes.update_route_with_apispec(
            metadata, {"body": {"type": "json", "schema": get_data_schema(body)}}
        )
    manager = CloudConnectionManager(False, MagicMock(), "test-token", None)
    manager.routes = Routes(1000)
    manager.conf.last_updated_at = 1
    manager.conf.revision = 0
    errors = []
    monkeypatch.setattr(thread_cache, "global_thread_cache", cache)
    monkeypatch.setattr(IPCClient, "_instance", None)

    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(2)
        IPCClient(listener.getsockname(), b"fixture")

        def receive():
            try:
                peer, _ = listener.accept()
                with peer, Connection(peer.dup().detach()) as connection:
                    threading.Event().wait(0.3)
                    action, payload = connection.recv()
                    assert action == "SYNC_DATA"
                    connection.send(sync_data.process(manager, payload, None))
            except (OSError, EOFError, AssertionError) as error:
                errors.append(error)

        server = threading.Thread(target=receive, daemon=True)
        server.start()
        try:
            with patch.object(
                process_worker.time, "sleep", side_effect=KeyboardInterrupt
            ):
                with pytest.raises(KeyboardInterrupt):
                    process_worker.aikido_process_worker_thread()
            assert cache.config.revision == 0
            assert manager.statistics.get_record()["requests"]["total"] == 1000
            assert sum(route["hits"] for route in manager.routes) == 1000
            assert all(
                len(route["apispec"]["body"]["schema"]["properties"]) == 50
                for route in manager.routes
            )
        finally:
            server.join(2)
        assert not server.is_alive()
        assert not errors
