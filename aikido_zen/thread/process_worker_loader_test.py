from unittest.mock import MagicMock, patch

import pytest

import aikido_zen.thread.process_worker_loader as loader
import aikido_zen.thread.thread_cache as thread_cache
from aikido_zen.context import Context, current_context


@pytest.fixture(autouse=True)
def run_around_tests():
    thread_cache.global_thread_cache.reset()
    current_context.set(None)
    yield
    thread_cache.global_thread_cache.reset()
    current_context.set(None)


def set_context():
    wsgi_request = {
        "REQUEST_METHOD": "GET",
        "HTTP_USER_AGENT": "test-agent",
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "localhost:8080",
        "PATH_INFO": "/",
        "QUERY_STRING": "",
        "REMOTE_ADDR": "1.2.3.4",
    }
    Context(req=wsgi_request, body=None, source="flask").set_as_current_context()


def load_worker_times(n, renew=None):
    """
    Calls load_worker() n times and returns how often the startup sync ran.
    A started thread joins the fake threading.enumerate(), the way a real one would,
    since finding that thread is what makes the worker set-up run only once.
    """
    set_context()
    running = []

    def fake_thread(target=None, name=None, **_kwargs):
        thread = MagicMock()
        thread.name = name
        thread.start.side_effect = lambda: running.append(thread)
        return thread

    renew = renew if renew is not None else MagicMock()
    with patch("aikido_zen.thread.thread_cache.renew", renew), patch(
        "threading.Thread", side_effect=fake_thread
    ), patch("threading.enumerate", side_effect=lambda: list(running)):
        for _ in range(n):
            loader.load_worker()
    return renew.call_count


def test_startup_sync_runs_on_the_first_request():
    assert load_worker_times(1) == 1


def test_startup_sync_is_attempted_only_once_per_process():
    assert load_worker_times(50) == 1


def test_startup_sync_is_skipped_once_the_config_is_loaded():
    thread_cache.global_thread_cache.config.last_updated_at = 1

    assert load_worker_times(10) == 0


def test_load_worker_does_nothing_without_a_context():
    with patch("aikido_zen.thread.thread_cache.renew") as renew, patch(
        "threading.Thread"
    ):
        loader.load_worker()

    assert renew.call_count == 0


def test_load_worker_does_not_raise_when_the_sync_fails():
    renew = MagicMock(side_effect=Exception("IPC down"))

    assert load_worker_times(1, renew=renew) == 1


def test_a_failed_sync_is_not_retried_on_the_request_path():
    renew = MagicMock(side_effect=Exception("IPC down"))

    assert load_worker_times(20, renew=renew) == 1
