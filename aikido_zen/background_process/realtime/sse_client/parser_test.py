from unittest.mock import MagicMock
from .parser import SSEParser, Event


def make_source(chunks):
    """Creates an iterable of byte chunks with a close() method, like an HTTP response."""
    source = MagicMock()
    source.__iter__.return_value = iter(chunks)
    return source


def test_read_single_chunk_single_event():
    source = make_source([b"data: hello\n\n"])
    parser = SSEParser(source)

    assert list(parser._read()) == [b"data: hello\n\n"]


def test_read_splits_multiple_events_in_one_chunk():
    source = make_source([b"data: one\n\ndata: two\n\n"])
    parser = SSEParser(source)

    assert list(parser._read()) == [b"data: one\n\n", b"data: two\n\n"]


def test_read_stitches_event_split_across_chunks():
    source = make_source([b"data: hel", b"lo\n\n"])
    parser = SSEParser(source)

    assert list(parser._read()) == [b"data: hello\n\n"]


def test_read_handles_carriage_return_delimiters():
    source = make_source([b"data: hello\r\r"])
    parser = SSEParser(source)

    assert list(parser._read()) == [b"data: hello\r\r"]


def test_read_handles_crlf_delimiters():
    source = make_source([b"data: hello\r\n\r\n"])
    parser = SSEParser(source)

    assert list(parser._read()) == [b"data: hello\r\n\r\n"]


def test_read_yields_trailing_incomplete_chunk():
    source = make_source([b"data: hello"])
    parser = SSEParser(source)

    assert list(parser._read()) == [b"data: hello"]


def test_events_basic_data_field():
    source = make_source([b"data: hello\n\n"])
    parser = SSEParser(source)

    events = list(parser.events())

    assert len(events) == 1
    assert events[0].data == "hello"
    assert events[0].event == "message"


def test_events_defaults_event_name_to_message():
    source = make_source([b"data: hello\n\n"])
    parser = SSEParser(source)

    [event] = parser.events()
    assert event.event == "message"


def test_events_custom_event_name_and_id():
    source = make_source([b"event: update\nid: 42\ndata: payload\n\n"])
    parser = SSEParser(source)

    [event] = parser.events()
    assert event.event == "update"
    assert event.id == "42"
    assert event.data == "payload"


def test_events_multiline_data_is_joined_with_newlines():
    source = make_source([b"data: line1\ndata: line2\n\n"])
    parser = SSEParser(source)

    [event] = parser.events()
    assert event.data == "line1\nline2"


def test_events_ignores_comment_lines():
    source = make_source([b": this is a comment\ndata: hello\n\n"])
    parser = SSEParser(source)

    [event] = parser.events()
    assert event.data == "hello"


def test_events_ignores_unknown_fields():
    source = make_source([b"foo: bar\ndata: hello\n\n"])
    parser = SSEParser(source)

    [event] = parser.events()
    assert event.data == "hello"
    assert not hasattr(event, "foo")


def test_events_strips_single_leading_space_from_value():
    source = make_source([b"data: hello\n\n"])
    parser = SSEParser(source)

    [event] = parser.events()
    assert event.data == "hello"


def test_events_keeps_extra_leading_spaces_beyond_first():
    source = make_source([b"data:  hello\n\n"])
    parser = SSEParser(source)

    [event] = parser.events()
    assert event.data == " hello"


def test_events_field_with_no_value_is_empty_string():
    source = make_source([b"event\ndata: hello\n\n"])
    parser = SSEParser(source)

    [event] = parser.events()
    assert event.event == "message"


def test_events_skips_events_with_no_data():
    source = make_source([b"event: ping\n\ndata: hello\n\n"])
    parser = SSEParser(source)

    events = list(parser.events())
    assert len(events) == 1
    assert events[0].data == "hello"


def test_events_multiple_events_in_stream():
    source = make_source([b"data: first\n\ndata: second\n\n"])
    parser = SSEParser(source)

    events = list(parser.events())
    assert [e.data for e in events] == ["first", "second"]


def test_events_retry_field():
    source = make_source([b"retry: 5000\ndata: hello\n\n"])
    parser = SSEParser(source)

    [event] = parser.events()
    assert event.retry == "5000"


def test_events_uses_configured_char_encoding():
    source = make_source(["data: héllo\n\n".encode("latin-1")])
    parser = SSEParser(source, char_enc="latin-1")

    [event] = parser.events()
    assert event.data == "héllo"


def test_close_delegates_to_event_source():
    source = make_source([])
    parser = SSEParser(source)

    parser.close()

    source.close.assert_called_once()


def test_event_str_with_data_and_id():
    event = Event(event_id="1", event="message", data="hello")
    assert str(event) == "message event #1, 5 bytes"


def test_event_str_without_data():
    event = Event()
    assert str(event) == "message event, no data"


def test_event_str_with_retry():
    event = Event(data="hi", retry=3000)
    assert str(event) == "message event, 2 bytes, retry in 3000ms"
