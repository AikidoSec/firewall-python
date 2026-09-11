from unittest.mock import MagicMock, patch

import pytest

from . import Context, current_context
from .track import track
import aikido_zen.context.track as track_module


@pytest.fixture(autouse=True)
def run_around_tests():
    current_context.set(None)
    track_module.logged_warning_track_called_without_context = False
    yield
    current_context.set(None)
    track_module.logged_warning_track_called_without_context = False


def set_context_and_lifecycle():
    wsgi_request = {
        "REQUEST_METHOD": "POST",
        "HTTP_USER_AGENT": "test-agent",
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "localhost:8080",
        "PATH_INFO": "/track-me",
        "QUERY_STRING": "",
        "REMOTE_ADDR": "1.2.3.4",
    }
    context = Context(req=wsgi_request, body=None, source="flask")
    context.set_as_current_context()
    return context


def test_track_invalid_event_name(caplog):
    track(123)
    assert "expects a non-empty string as event name." in caplog.text


def test_track_empty_event_name(caplog):
    track("")
    assert "expects a non-empty string as event name." in caplog.text


def test_track_without_context(caplog):
    track("my-event")
    assert "track(...) was called without a context." in caplog.text


def test_track_without_context_only_logs_once(caplog):
    track("my-event")
    track("my-event")
    assert caplog.text.count("track(...) was called without a context.") == 1


def test_track_without_comms():
    set_context_and_lifecycle()

    with patch("aikido_zen.background_process.comms.get_comms", return_value=None):
        # Should not raise
        track("my-event")


def test_track_sends_event_over_ipc():
    context = set_context_and_lifecycle()
    context.user = {"id": "user-1", "name": "Jane Doe"}

    comms = MagicMock()
    with patch("aikido_zen.background_process.comms.get_comms", return_value=comms):
        track("my-custom-event")

    comms.send_data_to_bg_process.assert_called_once()
    identifier, request, returns_data = comms.send_data_to_bg_process.call_args[0]
    assert identifier == "put_event"
    assert returns_data is False
    assert request.event == {
        "type": "custom",
        "name": "my-custom-event",
        "request": {
            "method": "POST",
            "url": "http://localhost:8080/track-me",
            "ipAddress": "1.2.3.4",
            "source": "flask",
            "route": "/track-me",
            "userAgent": "test-agent",
        },
        "user": {"id": "user-1", "name": "Jane Doe"},
    }
