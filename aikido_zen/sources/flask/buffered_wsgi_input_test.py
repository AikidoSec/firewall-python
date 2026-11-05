import copy
from io import BufferedReader, BytesIO, RawIOBase

import pytest

import aikido_zen.sources.flask.buffered_wsgi_input as buffered
from .buffered_wsgi_input import BufferedWsgiInput, buffer_wsgi_input

BODY = b'{"name": "a"}\n{"name": "b"}\n'


class FakeContext:
    def __init__(self, body=None):
        self.body = body
        self.bodies_set = []

    def set_body(self, body):
        self.body = body
        self.bodies_set.append(body)


class ReadOnlyStream:
    def __init__(self, data):
        self._stream = BytesIO(data)

    def read(self, *args):
        return self._stream.read(*args)

    def readline(self, *args):
        return self._stream.readline(*args)

    def __iter__(self):
        return iter(self._stream)


class ServerStream(ReadOnlyStream):
    def __init__(self, data):
        super().__init__(data)
        self.closed_count = 0

    def fileno(self):
        return 7

    def close(self):
        self.closed_count += 1


class RawStream(RawIOBase):
    def __init__(self, data):
        super().__init__()
        self._stream = BytesIO(data)

    def readable(self):
        return True

    def readinto(self, buffer):
        return self._stream.readinto(buffer)


class SizeRecordingStream(BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.sizes = []

    def read(self, size=-1):
        self.sizes.append(size)
        return super().read(size)


def read_all(stream, reader):
    if reader == "read":
        return stream.read()
    if reader == "read_minus_one":
        return stream.read(-1)
    if reader == "chunks":
        return b"".join(iter(lambda: stream.read(4), b""))
    if reader == "readline":
        return b"".join(iter(stream.readline, b""))
    if reader == "readlines":
        return b"".join(stream.readlines())
    if reader == "iterate":
        return b"".join(stream)
    if reader == "read1":
        return b"".join(iter(lambda: stream.read1(4), b""))
    if reader == "readall":
        return stream.readall()
    if reader == "next":
        return b"".join(iter(lambda: next(stream, b""), b""))
    readinto = stream.readinto1 if reader == "readinto1" else stream.readinto
    buffer = bytearray(4)
    data = b""
    while size := readinto(buffer):
        data += bytes(buffer[:size])
    return data


@pytest.mark.parametrize(
    "reader",
    [
        "read",
        "read_minus_one",
        "chunks",
        "readline",
        "readlines",
        "iterate",
        "next",
        "readinto",
    ],
)
@pytest.mark.parametrize("content_length", [len(BODY), None])
def test_passes_reads_through_and_records_the_body_once(reader, content_length):
    context = FakeContext()
    stream = BufferedWsgiInput(BytesIO(BODY), context, content_length, True)
    assert read_all(stream, reader) == BODY
    assert context.bodies_set == [BODY]


def test_later_reads_skip_the_wrapper():
    stream = BufferedWsgiInput(BytesIO(BODY), FakeContext(), len(BODY), False)
    stream.read(1)
    assert isinstance(stream.readinto.__self__, BytesIO)
    assert isinstance(stream.readline.__self__, BytesIO)


def test_seek_and_tell_follow_the_reads():
    stream = BufferedWsgiInput(BytesIO(BODY), FakeContext(), len(BODY), False)
    assert stream.read(3) == BODY[:3]
    assert stream.tell() == 3
    stream.seek(0)
    assert stream.read() == BODY


def test_seek_and_tell_stay_missing_when_the_server_stream_has_none():
    stream = BufferedWsgiInput(ReadOnlyStream(BODY), FakeContext(), len(BODY), False)
    stream.read(2)
    assert not hasattr(stream, "seek")
    assert not hasattr(stream, "tell")


@pytest.mark.parametrize("limit", [buffered.MAX_BUFFERED_BODY_SIZE, 8])
def test_peek_after_a_read_returns_the_next_bytes(monkeypatch, limit):
    monkeypatch.setattr(buffered, "MAX_BUFFERED_BODY_SIZE", limit)
    original = BufferedReader(BytesIO(BODY))
    stream = BufferedWsgiInput(original, FakeContext(), len(BODY), False)
    assert stream.read(5) == BODY[:5]
    assert stream.peek(1)[:1] == BODY[5:6]
    assert stream.read() == BODY[5:]


def test_fileno_and_close_reach_the_server_stream():
    original = ServerStream(BODY)
    stream = BufferedWsgiInput(original, FakeContext(), len(BODY), False)
    assert stream.fileno() == 7
    stream.read(1)
    assert stream.fileno() == 7
    stream.close()
    assert original.closed_count == 1


@pytest.mark.parametrize(
    "reader, server_stream",
    [("read1", BytesIO), ("readinto1", BytesIO), ("readall", RawStream)],
)
def test_other_read_methods_record_the_body(reader, server_stream):
    context = FakeContext()
    stream = BufferedWsgiInput(server_stream(BODY), context, len(BODY), False)
    assert read_all(stream, reader) == BODY
    assert context.bodies_set == [BODY]


@pytest.mark.parametrize("name", ["read1", "readinto1", "readall", "peek"])
def test_read_method_stays_missing_when_the_server_stream_has_none(name):
    stream = BufferedWsgiInput(ReadOnlyStream(BODY), FakeContext(), len(BODY), False)
    assert not hasattr(stream, name)


def test_unknown_length_on_an_unterminated_stream_is_not_read_ahead():
    context = FakeContext()
    stream = BufferedWsgiInput(BytesIO(BODY), context, None, False)
    assert stream.read(5) == BODY[:5]
    assert context.bodies_set == []


@pytest.mark.parametrize(
    "headers",
    [
        {"CONTENT_LENGTH": "0"},
        {"CONTENT_LENGTH": "4"},
        {"CONTENT_LENGTH": "-1"},
        {"CONTENT_LENGTH": "4", "HTTP_TRANSFER_ENCODING": "chunked"},
        {},
    ],
)
@pytest.mark.parametrize("terminated", [True, False])
def test_terminated_stream_is_read_to_the_end(headers, terminated):
    context = FakeContext()
    environ = {
        "wsgi.input": BytesIO(BODY),
        "wsgi.input_terminated": terminated,
        **headers,
    }
    buffer_wsgi_input(environ, context)
    assert environ["wsgi.input"].read() == BODY
    assert context.bodies_set == [BODY]


@pytest.mark.parametrize(
    "headers",
    [
        {"CONTENT_LENGTH": "0"},
        {"CONTENT_LENGTH": "-1"},
        {"CONTENT_LENGTH": "abc"},
        {"CONTENT_LENGTH": "4", "HTTP_TRANSFER_ENCODING": "chunked"},
    ],
)
def test_unusable_length_on_an_unterminated_stream_is_passed_through(headers):
    context = FakeContext()
    environ = {"wsgi.input": BytesIO(BODY), **headers}
    buffer_wsgi_input(environ, context)
    assert environ["wsgi.input"].read() == BODY
    assert context.bodies_set == []


def test_terminated_stream_over_the_limit_is_not_read_ahead(monkeypatch):
    monkeypatch.setattr(buffered, "MAX_BUFFERED_BODY_SIZE", 8)
    original = BytesIO(BODY)
    context = FakeContext()
    stream = BufferedWsgiInput(original, context, len(BODY), True)
    assert stream.read(2) == BODY[:2]
    assert original.tell() == 2
    assert context.bodies_set == []


@pytest.mark.parametrize(
    "content_length, terminated", [(None, True), (1024 * 1024, False)]
)
def test_stream_is_read_in_pieces(content_length, terminated):
    original = SizeRecordingStream(BODY)
    stream = BufferedWsgiInput(original, FakeContext(), content_length, terminated)
    assert stream.read(5) == BODY[:5]
    assert max(original.sizes) <= buffered.READ_CHUNK_SIZE


def test_stream_without_readinto_is_recorded():
    context = FakeContext()
    stream = BufferedWsgiInput(ReadOnlyStream(BODY), context, len(BODY), False)
    assert read_all(stream, "readinto") == BODY
    assert context.bodies_set == [BODY]


@pytest.mark.parametrize("copier", [copy.copy, copy.deepcopy])
def test_stream_can_be_copied(copier):
    stream = BufferedWsgiInput(BytesIO(BODY), FakeContext(), len(BODY), False)
    assert copier(stream).read() == BODY


def test_partial_read_records_the_whole_body():
    context = FakeContext()
    stream = BufferedWsgiInput(BytesIO(BODY), context, len(BODY), False)
    assert stream.read(5) == BODY[:5]
    assert context.bodies_set == [BODY]
    assert stream.read() == BODY[5:]


@pytest.mark.parametrize("reader", ["chunks", "readline", "iterate", "readinto"])
@pytest.mark.parametrize("content_length", [len(BODY), None])
def test_body_over_the_limit_is_passed_through_but_not_recorded(
    monkeypatch, reader, content_length
):
    monkeypatch.setattr(buffered, "MAX_BUFFERED_BODY_SIZE", 8)
    context = FakeContext()
    stream = BufferedWsgiInput(ReadOnlyStream(BODY), context, content_length, True)
    assert read_all(stream, reader) == BODY
    assert context.bodies_set == []


def test_body_already_captured_is_kept():
    context = FakeContext(body={"name": "parsed"})
    stream = BufferedWsgiInput(BytesIO(BODY), context, len(BODY), False)
    assert stream.read() == BODY
    assert context.bodies_set == []


@pytest.mark.parametrize(
    "content_type, wrapped",
    [
        ("application/json", True),
        ("", True),
        ("multipart/form-data; boundary=x", False),
        ("Application/X-WWW-Form-Urlencoded", False),
    ],
)
def test_buffer_wsgi_input_skips_form_bodies(content_type, wrapped):
    environ = {
        "wsgi.input": BytesIO(BODY),
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(BODY)),
    }
    buffer_wsgi_input(environ, FakeContext())
    assert isinstance(environ["wsgi.input"], BufferedWsgiInput) is wrapped


def test_buffer_wsgi_input_without_input_stream():
    environ = {}
    buffer_wsgi_input(environ, FakeContext())
    assert environ == {}
