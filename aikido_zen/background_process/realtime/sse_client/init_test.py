import socket
import urllib.error
from unittest.mock import MagicMock, patch

from aikido_zen.helpers.token import Token
from . import (
    _connect,
    _reconnect_loop,
    connect_to_sse,
    INITIAL_RECONNECT_SECS,
    READ_TIMEOUT_SECS,
)

REALTIME_URL_PATCH = patch(
    "aikido_zen.background_process.realtime.get_realtime_url",
    return_value="https://runtime.aikido.dev/",
)


def make_response(status_code, chunks=None):
    response = MagicMock()
    response.getcode.return_value = status_code
    response.__enter__.return_value = response
    response.__exit__.side_effect = lambda *args: response.close()
    if chunks is not None:
        response.__iter__.return_value = iter(chunks)
    return response


def test_connect_dispatches_events_and_reports_disconnected_on_stream_end():
    response = make_response(200, [b"data: hello\n\n", b"data: world\n\n"])
    events = []

    with REALTIME_URL_PATCH, patch("urllib.request.urlopen", return_value=response):
        outcome, status_code = _connect(Token("123"), events.append, 5)

    assert outcome == "disconnected"
    assert status_code == 200
    assert [e.data for e in events] == ["hello", "world"]
    response.close.assert_called_once()  # closed via parser.close()


def test_connect_sends_expected_request():
    response = make_response(200, [])
    captured_request = {}

    def fake_urlopen(request, timeout):
        captured_request["request"] = request
        captured_request["timeout"] = timeout
        return response

    with REALTIME_URL_PATCH, patch("urllib.request.urlopen", side_effect=fake_urlopen):
        _connect(Token("my-token"), MagicMock(), 42)

    request = captured_request["request"]
    assert request.full_url == "https://runtime.aikido.dev/api/runtime/stream"
    assert request.get_header("Authorization") == "my-token"
    assert request.get_header("Accept") == "text/event-stream"
    assert captured_request["timeout"] == 42


def test_connect_non_200_status_closes_response_without_reading_body():
    response = make_response(500)

    with REALTIME_URL_PATCH, patch("urllib.request.urlopen", return_value=response):
        outcome, status_code = _connect(Token("123"), MagicMock(), 5)

    assert outcome == "disconnected"
    assert status_code == 500
    response.close.assert_called_once()


def test_connect_http_error_returns_disconnected_with_status():
    http_error = urllib.error.HTTPError(
        url="https://runtime.aikido.dev/api/runtime/stream",
        code=403,
        msg="Forbidden",
        hdrs=None,
        fp=None,
    )

    with REALTIME_URL_PATCH, patch("urllib.request.urlopen", side_effect=http_error):
        outcome, status_code = _connect(Token("123"), MagicMock(), 5)

    assert outcome == "disconnected"
    assert status_code == 403


def test_connect_connection_error_returns_error_outcome():
    with REALTIME_URL_PATCH, patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        outcome, status_code = _connect(Token("123"), MagicMock(), 5)

    assert outcome == "error"
    assert status_code is None


def test_connect_read_timeout_mid_stream_returns_error():
    response = make_response(200)
    response.__iter__.side_effect = socket.timeout("timed out")

    with REALTIME_URL_PATCH, patch("urllib.request.urlopen", return_value=response):
        outcome, status_code = _connect(Token("123"), MagicMock(), 5)

    assert outcome == "error"
    assert status_code is None
    response.close.assert_called_once()


def test_connect_generic_stream_error_returns_disconnected_with_status():
    response = make_response(200)
    response.__iter__.side_effect = ConnectionResetError("reset")

    with REALTIME_URL_PATCH, patch("urllib.request.urlopen", return_value=response):
        outcome, status_code = _connect(Token("123"), MagicMock(), 5)

    assert outcome == "disconnected"
    assert status_code == 200


def test_reconnect_loop_stops_immediately_on_401_or_403():
    for status_code in (401, 403):
        connect_calls = []

        def fake_connect(token, on_event, read_timeout_secs):
            connect_calls.append(status_code)
            return "disconnected", status_code

        with patch(
            "aikido_zen.background_process.realtime.sse_client._connect",
            side_effect=fake_connect,
        ), patch(
            "aikido_zen.background_process.realtime.sse_client.time.sleep"
        ) as mock_sleep:
            _reconnect_loop(Token("123"), MagicMock(), INITIAL_RECONNECT_SECS, 5)

        assert connect_calls == [status_code]
        mock_sleep.assert_not_called()


def test_reconnect_loop_backoff_doubles_between_reconnects():
    outcomes = iter(
        [("error", None), ("error", None), ("disconnected", 401)],
    )
    sleep_calls = []
    monotonic_values = iter([0, 0, 10, 10, 20])

    with patch(
        "aikido_zen.background_process.realtime.sse_client._connect",
        side_effect=lambda *a: next(outcomes),
    ), patch(
        "aikido_zen.background_process.realtime.sse_client.time.sleep",
        side_effect=sleep_calls.append,
    ), patch(
        "aikido_zen.background_process.realtime.sse_client.time.monotonic",
        side_effect=lambda: next(monotonic_values),
    ), patch(
        "aikido_zen.background_process.realtime.sse_client.random.random",
        return_value=0,
    ):
        _reconnect_loop(Token("123"), MagicMock(), 5, 5)

    assert sleep_calls == [5, 10]


def test_reconnect_loop_resets_backoff_after_stable_connection():
    outcomes = iter(
        [
            ("error", None),
            ("error", None),
            ("error", None),
            ("disconnected", 401),
        ],
    )
    sleep_calls = []
    # start1=0 end1=0 (unstable) | start2=10 end2=10 (unstable) | start3=20 end3=60 (stable, resets) | start4=unused
    monotonic_values = iter([0, 0, 10, 10, 20, 60, 999])

    with patch(
        "aikido_zen.background_process.realtime.sse_client._connect",
        side_effect=lambda *a: next(outcomes),
    ), patch(
        "aikido_zen.background_process.realtime.sse_client.time.sleep",
        side_effect=sleep_calls.append,
    ), patch(
        "aikido_zen.background_process.realtime.sse_client.time.monotonic",
        side_effect=lambda: next(monotonic_values),
    ), patch(
        "aikido_zen.background_process.realtime.sse_client.random.random",
        return_value=0,
    ):
        _reconnect_loop(Token("123"), MagicMock(), 5, 5)

    assert sleep_calls == [5, 10, 5]


def test_reconnect_loop_logs_unexpected_exception(caplog):
    with patch(
        "aikido_zen.background_process.realtime.sse_client._connect",
        side_effect=RuntimeError("boom"),
    ):
        _reconnect_loop(Token("123"), MagicMock(), 5, 5)

    assert "SSE loop error : boom" in caplog.text


def test_connect_to_sse_starts_a_daemon_thread_running_the_reconnect_loop():
    with patch(
        "aikido_zen.background_process.realtime.sse_client._reconnect_loop"
    ) as mock_loop:
        token = Token("123")
        on_event = MagicMock()
        thread = connect_to_sse(token, on_event)
        thread.join(timeout=2)

    assert thread.daemon is True
    mock_loop.assert_called_once_with(
        token, on_event, INITIAL_RECONNECT_SECS, READ_TIMEOUT_SECS
    )
