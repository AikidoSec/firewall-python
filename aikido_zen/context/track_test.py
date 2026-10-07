from unittest.mock import MagicMock, patch

import pytest

from . import Context, current_context, get_current_context
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
    with patch(
        "aikido_zen.background_process.comms.get_comms", return_value=MagicMock()
    ):
        track("my-event")

    assert "track(...) was called without a context." in caplog.text


def test_track_without_context_only_logs_once(caplog):
    with patch(
        "aikido_zen.background_process.comms.get_comms", return_value=MagicMock()
    ):
        track("my-event")
        track("my-event")

    assert caplog.text.count("track(...) was called without a context.") == 1


def test_track_without_comms(caplog):
    with patch("aikido_zen.background_process.comms.get_comms", return_value=None):
        track("my-event")

    assert "track(...) was called without a context." not in caplog.text


def test_track_sends_event_over_ipc():
    context = set_context_and_lifecycle()
    context.user = {"id": "user-1", "name": "Jane Doe"}

    comms = MagicMock()
    with patch(
        "aikido_zen.thread.thread_cache.get_cache",
        return_value=cache_with_bypassed_ips(),
    ), patch(
        "aikido_zen.background_process.comms.get_comms", return_value=comms
    ), patch(
        "aikido_zen.helpers.create_custom_event.get_unixtime_ms",
        return_value=111,
    ):
        track("my-custom-event")

    comms.send_data_to_bg_process.assert_called_once()
    identifier, request, returns_data = comms.send_data_to_bg_process.call_args[0]
    assert identifier == "put_event"
    assert returns_data is False
    assert request.event == {
        "type": "custom",
        "time": 111,
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


def track_n_times(n, event_name="my-custom-event"):
    """Runs track() n times in ONE request and returns the events that were sent"""
    set_context_and_lifecycle()
    comms = MagicMock()
    with patch(
        "aikido_zen.thread.thread_cache.get_cache",
        return_value=cache_with_bypassed_ips(),
    ), patch("aikido_zen.background_process.comms.get_comms", return_value=comms):
        for _ in range(n):
            track(event_name)

    return [c[0][1].event for c in comms.send_data_to_bg_process.call_args_list]


def test_track_sends_every_event_below_the_limit():
    sent = track_n_times(track_module.MAX_EVENTS_PER_REQUEST)

    assert len(sent) == track_module.MAX_EVENTS_PER_REQUEST


def test_track_stops_sending_events_above_the_limit():
    sent = track_n_times(track_module.MAX_EVENTS_PER_REQUEST + 50)

    assert len(sent) == track_module.MAX_EVENTS_PER_REQUEST


def test_all_event_names_share_one_budget():
    set_context_and_lifecycle()
    comms = MagicMock()
    with patch(
        "aikido_zen.thread.thread_cache.get_cache",
        return_value=cache_with_bypassed_ips(),
    ), patch("aikido_zen.background_process.comms.get_comms", return_value=comms):
        for _ in range(track_module.MAX_EVENTS_PER_REQUEST):
            track("payment.failed")
        track("order.completed")

    names = [
        c[0][1].event["name"] for c in comms.send_data_to_bg_process.call_args_list
    ]
    assert len(names) == track_module.MAX_EVENTS_PER_REQUEST
    assert "order.completed" not in names


def test_track_warns_once_per_request_when_the_limit_is_reached(caplog):
    track_n_times(track_module.MAX_EVENTS_PER_REQUEST + 5)

    assert caplog.text.count("was called more than") == 1


def test_track_warns_again_on_the_next_request(caplog):
    track_n_times(track_module.MAX_EVENTS_PER_REQUEST + 5)
    track_n_times(track_module.MAX_EVENTS_PER_REQUEST + 5)

    assert caplog.text.count("was called more than") == 2


def test_track_does_not_warn_below_the_limit(caplog):
    track_n_times(track_module.MAX_EVENTS_PER_REQUEST)

    assert "was called more than" not in caplog.text


def test_the_limit_is_per_request_not_per_process():
    first = track_n_times(track_module.MAX_EVENTS_PER_REQUEST + 10)
    second = track_n_times(1)

    assert len(first) == track_module.MAX_EVENTS_PER_REQUEST
    assert len(second) == 1


def test_a_bypassed_ip_does_not_use_up_the_limit():
    set_context_and_lifecycle()
    comms = MagicMock()
    with patch(
        "aikido_zen.thread.thread_cache.get_cache",
        return_value=cache_with_bypassed_ips("1.2.3.4"),
    ), patch("aikido_zen.background_process.comms.get_comms", return_value=comms):
        for _ in range(track_module.MAX_EVENTS_PER_REQUEST + 5):
            track("my-custom-event")

    assert get_current_context().tracked_events == 0


def test_track_sends_the_event_with_a_short_timeout():
    set_context_and_lifecycle()

    comms = MagicMock()
    with patch(
        "aikido_zen.thread.thread_cache.get_cache",
        return_value=cache_with_bypassed_ips(),
    ), patch("aikido_zen.background_process.comms.get_comms", return_value=comms):
        track("my-custom-event")

    comms.send_data_to_bg_process.assert_called_once()
    assert comms.send_data_to_bg_process.call_args[1]["timeout_in_sec"] == 0.05


def test_track_sends_nothing_when_the_event_could_not_be_built():
    set_context_and_lifecycle()

    comms = MagicMock()
    with patch(
        "aikido_zen.thread.thread_cache.get_cache",
        return_value=cache_with_bypassed_ips(),
    ), patch(
        "aikido_zen.background_process.comms.get_comms", return_value=comms
    ), patch(
        "aikido_zen.context.track.create_custom_event", return_value=None
    ):
        track("my-custom-event")

    comms.send_data_to_bg_process.assert_not_called()
