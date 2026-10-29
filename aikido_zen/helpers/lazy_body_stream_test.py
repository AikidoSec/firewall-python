from io import BytesIO
from unittest.mock import Mock

import pytest

from .lazy_body_stream import LazyBodyStream


@pytest.mark.parametrize(
    "method,args", [("read", (2,)), ("readline", ()), ("readlines", ())]
)
def test_capture_runs_before_reading_and_only_once(method, args):
    original = BytesIO(b"first\nsecond\n")
    callback = Mock(side_effect=lambda: original.seek(0))
    stream = LazyBodyStream(original, callback)
    assert original.tell() == 0
    expected = getattr(BytesIO(b"first\nsecond\n"), method)(*args)
    assert getattr(stream, method)(*args) == expected
    stream.read()
    callback.assert_called_once_with()


def test_readinto_is_captured():
    callback = Mock()
    stream = LazyBodyStream(BytesIO(b"body"), callback)
    buffer = bytearray(4)
    assert stream.readinto(buffer) == 4
    assert buffer == b"body"
    callback.assert_called_once_with()


def test_iteration_is_captured():
    callback = Mock()
    stream = LazyBodyStream(BytesIO(b"first\nsecond\n"), callback)
    assert list(stream) == [b"first\n", b"second\n"]
    callback.assert_called_once_with()


def test_next_is_captured():
    callback = Mock()
    stream = LazyBodyStream(BytesIO(b"first\nsecond\n"), callback)
    assert next(stream) == b"first\n"
    assert next(stream) == b"second\n"
    callback.assert_called_once_with()


def test_loader_can_read_the_same_stream_without_recursion():
    captured = []
    stream = LazyBodyStream(BytesIO(b"body"), lambda: captured.append(stream.read()))
    assert stream.read() == b""
    assert captured == [b"body"]


def test_read_uses_a_stream_replaced_by_the_loader():
    def replace():
        stream.__wrapped__ = BytesIO(b"replacement")

    stream = LazyBodyStream(BytesIO(b"original"), replace)
    assert stream.read(3) == b"rep"
    assert stream.read() == b"lacement"


def test_does_not_add_unsupported_read_methods():
    class Input:
        def read(self, size=-1):
            return b"body"

    stream = LazyBodyStream(Input(), Mock())
    assert not hasattr(stream, "readinto")
    assert stream.read() == b"body"


def test_non_read_operations_do_not_load_body():
    callback = Mock()
    stream = LazyBodyStream(BytesIO(b"body"), callback)
    assert stream.tell() == 0
    assert stream.readable()
    stream.close()
    assert stream.closed
    callback.assert_not_called()


def test_original_read_error_is_propagated():
    original = BytesIO(b"body")
    original.close()
    callback = Mock()
    stream = LazyBodyStream(original, callback)
    with pytest.raises(ValueError):
        stream.read()
    callback.assert_called_once_with()
