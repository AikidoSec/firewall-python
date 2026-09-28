from unittest.mock import MagicMock, patch

import pytest

from . import Context, current_context
from .track import track
from aikido_zen.thread.thread_cache import ThreadCache
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


def cache_with_bypassed_ips(*ips):
    cache = ThreadCache()
    cache.config.set_bypassed_ips(list(ips))
    return cache


def sent_event_with_cache(cache):
    set_context_and_lifecycle()
    comms = MagicMock()
    with patch("aikido_zen.thread.thread_cache.get_cache", return_value=cache), patch(
        "aikido_zen.background_process.comms.get_comms", return_value=comms
    ):
        track("my-custom-event")

    if not comms.send_data_to_bg_process.called:
        return None
    return comms.send_data_to_bg_process.call_args[0][1].event


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
    with patch(
        "aikido_zen.thread.thread_cache.get_cache",
        return_value=cache_with_bypassed_ips(),
    ), patch("aikido_zen.background_process.comms.get_comms", return_value=comms):
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
            "ipAddress": "1.2.3.4",
            "userAgent": "test-agent",
            "source": "flask",
            "route": "/track-me",
        },
        "user": {"id": "user-1", "name": "Jane Doe"},
    }


def test_track_does_not_send_an_event_for_a_bypassed_ip():
    assert sent_event_with_cache(cache_with_bypassed_ips("1.2.3.4")) is None


def test_track_sends_an_event_for_an_ip_that_is_not_bypassed():
    assert sent_event_with_cache(cache_with_bypassed_ips("5.6.7.8")) is not None


def test_track_sends_an_event_before_the_config_was_received():
    cache = ThreadCache()

    assert cache.config.last_updated_at == -1
    assert sent_event_with_cache(cache) is not None


def test_track_sends_an_event_without_a_thread_cache():
    assert sent_event_with_cache(None) is not None


def test_track_does_not_raise_when_the_bypass_check_fails():
    cache = MagicMock()
    cache.is_bypassed_ip.side_effect = Exception("Test exception")

    assert sent_event_with_cache(cache) is None


def test_track_does_not_raise_without_a_client_ip():
    context = set_context_and_lifecycle()
    context.remote_address = None

    with patch("aikido_zen.thread.thread_cache.get_cache", return_value=ThreadCache()):
        track("my-event")


def test_track_does_not_send_the_url():
    event = sent_event_with_cache(cache_with_bypassed_ips())

    assert "url" not in event["request"]
