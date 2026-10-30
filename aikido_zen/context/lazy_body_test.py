import pickle
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from threading import Event
from unittest.mock import Mock

import pytest

from . import Context


def test_body_is_loaded_once_on_first_access():
    context = Context()
    loader = Mock(return_value=b'{"name":"input"}')
    context.set_body_loader(loader)
    loader.assert_not_called()
    assert context.body == {"name": "input"}
    assert context.body == {"name": "input"}
    loader.assert_called_once_with()


def test_body_loader_is_not_reentered():
    context = Context()
    loader = Mock(side_effect=lambda: context.body or b"body")
    context.set_body_loader(loader)
    assert context.body == "body"
    loader.assert_called_once_with()


def test_concurrent_body_access_waits_for_the_complete_body():
    context = Context()
    started = Event()
    second_started = Event()
    release = Event()

    def load():
        started.set()
        assert release.wait(5)
        return b'{"name":"input"}'

    loader = Mock(side_effect=load)
    context.set_body_loader(loader)

    def read_second():
        second_started.set()
        return context.body

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(lambda: context.body)
        assert started.wait(5)
        second = pool.submit(read_second)
        try:
            assert second_started.wait(5)
            with pytest.raises(FutureTimeout):
                second.result(0.1)
        finally:
            release.set()
        assert first.result(5) == {"name": "input"}
        assert second.result(5) == {"name": "input"}
    loader.assert_called_once_with()


def test_explicit_body_replaces_pending_loader():
    context = Context()
    loader = Mock(return_value=b"old")
    context.set_body_loader(loader)
    context.set_body(b"replacement")
    assert context.body == "replacement"
    loader.assert_not_called()


def test_failed_loader_is_not_retried_on_every_inspection():
    context = Context()
    loader = Mock(side_effect=ValueError("body unavailable"))
    context.set_body_loader(loader)
    assert context.body is None
    assert context.body is None
    loader.assert_called_once_with()


def test_pickle_loads_body_without_serializing_loader():
    context = Context()
    loader = Mock(return_value=b'{"name":"input"}')
    context.set_body_loader(loader)
    restored = pickle.loads(pickle.dumps(context))
    assert restored.body == {"name": "input"}
    assert "_body_loader" not in restored.__dict__
    loader.assert_called_once_with()


def test_body_loader_is_used_by_schema_discovery_without_application_read():
    from aikido_zen.api_discovery.get_api_info import get_body_info
    from aikido_zen.helpers.headers import Headers

    context = Context()
    context.headers = Headers({"CONTENT_TYPE": ["application/json"]})
    loader = Mock(return_value=b'{"name":"input"}')
    context.set_body_loader(loader)
    assert get_body_info(context) == {
        "type": "json",
        "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
    }
    loader.assert_called_once_with()
