"""
Integration tests that exercise the SSE client against a real HTTP server
(as opposed to init_test.py, which mocks urllib.request.urlopen), so that real
socket/timeout/connection-refused behavior is covered, not just our own mocks.
"""

import http.server
import json
import threading
import time
from unittest.mock import patch

from aikido_zen.helpers.token import Token
from . import _connect, _reconnect_loop

REALTIME_URL_PATCH_TARGET = "aikido_zen.background_process.realtime.get_realtime_url"


class _TestServer(http.server.ThreadingHTTPServer):
    daemon_threads = True  # Don't let lingering handler threads block process exit


def make_handler(do_get):
    """Builds a BaseHTTPRequestHandler class that delegates GET handling to `do_get(handler)`."""

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def do_GET(self):  # pylint: disable=invalid-name
            do_get(self)

        def log_message(self, *args, **kwargs):
            pass

    return Handler


def start_server(handler_class):
    server = _TestServer(("127.0.0.1", 0), handler_class)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"


def stop_server(server):
    server.shutdown()
    server.server_close()


def wait_until(predicate, timeout=2.0, interval=0.01):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def test_happy_path_receives_events_with_auth_header():
    captured = {}
    events = []

    def do_get(handler):
        captured["auth"] = handler.headers.get("Authorization")
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-cache")
        handler.end_headers()
        handler.wfile.write(b": ping\n\n")
        handler.wfile.write(
            b'event: config-updated\ndata: {"configUpdatedAt": 100}\n\n'
        )
        handler.wfile.flush()
        time.sleep(0.2)
        handler.wfile.write(
            b'event: config-updated\ndata: {"configUpdatedAt": 200}\n\n'
        )
        handler.wfile.flush()

    server, url = start_server(make_handler(do_get))
    try:
        with patch(REALTIME_URL_PATCH_TARGET, return_value=url):
            outcome, status_code = _connect(
                Token("my-secret-token"), events.append, read_timeout_secs=5
            )
    finally:
        stop_server(server)

    assert outcome == "disconnected"
    assert status_code == 200
    assert captured["auth"] == "my-secret-token"
    assert len(events) == 2
    assert events[0].event == "config-updated"
    assert json.loads(events[0].data) == {"configUpdatedAt": 100}
    assert json.loads(events[1].data) == {"configUpdatedAt": 200}


def test_stops_reconnecting_on_401():
    connection_count = {"n": 0}

    def do_get(handler):
        connection_count["n"] += 1
        handler.send_response(401)
        handler.end_headers()

    server, url = start_server(make_handler(do_get))
    try:
        with patch(REALTIME_URL_PATCH_TARGET, return_value=url):
            _reconnect_loop(
                Token("bad-token"),
                lambda event: None,
                initial_reconnect_secs=0.05,
                read_timeout_secs=1,
            )
    finally:
        stop_server(server)

    assert connection_count["n"] == 1


def test_reconnects_after_non_200_status():
    connection_count = {"n": 0}

    def do_get(handler):
        connection_count["n"] += 1
        if connection_count["n"] == 1:
            handler.send_response(500)
            handler.end_headers()
            return
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-cache")
        handler.end_headers()
        handler.wfile.write(b": ping\n\n")
        handler.wfile.flush()

    server, url = start_server(make_handler(do_get))
    try:
        with patch(REALTIME_URL_PATCH_TARGET, return_value=url):
            thread = threading.Thread(
                target=_reconnect_loop,
                args=(Token("test-token"), lambda event: None, 0.05, 1),
                daemon=True,
            )
            thread.start()
            assert wait_until(lambda: connection_count["n"] >= 2)
    finally:
        stop_server(server)


def test_connection_refused():
    probe = _TestServer(("127.0.0.1", 0), make_handler(lambda handler: None))
    port = probe.server_address[1]
    probe.server_close()

    with patch(REALTIME_URL_PATCH_TARGET, return_value=f"http://127.0.0.1:{port}/"):
        outcome, status_code = _connect(
            Token("test-token"), lambda event: None, read_timeout_secs=1
        )

    assert outcome == "error"
    assert status_code is None


def test_reconnects_on_read_timeout():
    connection_count = {"n": 0}

    def do_get(handler):
        connection_count["n"] += 1
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-cache")
        handler.end_headers()
        if connection_count["n"] == 1:
            time.sleep(1)
        else:
            handler.wfile.write(b": ping\n\n")
            handler.wfile.flush()

    server, url = start_server(make_handler(do_get))
    try:
        with patch(REALTIME_URL_PATCH_TARGET, return_value=url):
            thread = threading.Thread(
                target=_reconnect_loop,
                args=(Token("test-token"), lambda event: None, 0.05, 0.2),
                daemon=True,
            )
            thread.start()
            assert wait_until(lambda: connection_count["n"] >= 2)
    finally:
        stop_server(server)


def test_reconnects_when_server_closes_connection():
    connection_count = {"n": 0}

    def do_get(handler):
        connection_count["n"] += 1
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-cache")
        handler.end_headers()
        handler.wfile.write(b": ping\n\n")
        handler.wfile.flush()

    server, url = start_server(make_handler(do_get))
    try:
        with patch(REALTIME_URL_PATCH_TARGET, return_value=url):
            thread = threading.Thread(
                target=_reconnect_loop,
                args=(Token("test-token"), lambda event: None, 0.05, 1),
                daemon=True,
            )
            thread.start()
            assert wait_until(lambda: connection_count["n"] >= 2)
    finally:
        stop_server(server)
