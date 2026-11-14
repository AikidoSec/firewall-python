import pytest
import pickle
import json
from aikido_zen.context import Context, get_current_context, current_context

LEVELS_TOO_DEEP_TO_PARSE = 1_000_000

basic_wsgi_req = {
    "REQUEST_METHOD": "GET",
    "HTTP_HEADER_1": "header 1 value",
    "HTTP_HEADER_2": "Header 2 value",
    "RANDOM_VALUE": "Random value",
    "HTTP_COOKIE": "sessionId=abc123xyz456;",
    "wsgi.url_scheme": "http",
    "HTTP_HOST": "localhost:8080",
    "PATH_INFO": "/hello",
    "QUERY_STRING": "user=JohnDoe&age=30&age=35",
    "CONTENT_TYPE": "application/json",
    "REMOTE_ADDR": "198.51.100.23",
    "HTTP_USER_AGENT": "Mozilla/5.0",
}


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    # Make sure to reset context after every test so it does not
    # interfere with other tests
    current_context.set(None)


def test_get_current_context_no_context():
    # Test get_current_context() when no context is set
    assert get_current_context() is None


def test_wsgi_context_1():
    wsgi_request = {
        "REQUEST_METHOD": "POST",
        "HTTP_HEADER_1": "header 1 value",
        "HTTP_HEADER_2": "Header 2 value",
        "RANDOM_VALUE": "Random value",
        "HTTP_COOKIE": "sessionId=abc123xyz456;",
        "wsgi.url_scheme": "https",
        "HTTP_HOST": "example.com",
        "PATH_INFO": "/hello",
        "QUERY_STRING": "user=JohnDoe&age=30&age=35",
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "REMOTE_ADDR": "198.51.100.23",
    }
    context = Context(req=wsgi_request, body=123, source="django")
    assert context.__dict__ == {
        "is_behind_trusted_proxy": True,
        "source": "django",
        "method": "POST",
        "headers": {
            "HEADER_1": ["header 1 value"],
            "HEADER_2": ["Header 2 value"],
            "COOKIE": ["sessionId=abc123xyz456;"],
            "HOST": ["example.com"],
            "CONTENT_TYPE": ["application/x-www-form-urlencoded"],
        },
        "cookies": {"sessionId": "abc123xyz456"},
        "url": "https://example.com/hello",
        "query": {"user": ["JohnDoe"], "age": ["30", "35"]},
        "body": 123,
        "route": "/hello",
        "subdomains": [],
        "user": None,
        "rate_limit_group": None,
        "remote_address": "198.51.100.23",
        "parsed_userinput": {},
        "xml": {},
        "outgoing_req_redirects": [],
        "executed_middleware": False,
        "tracked_events": 0,
        "tracked_events_limit_warning_logged": False,
        "route_params": [],
        "protection_forced_off": None,
    }
    assert context.get_user_agent() is None


def test_wsgi_context_2():
    context = Context(req=basic_wsgi_req, body={"test": True}, source="flask")
    assert context.__dict__ == {
        "is_behind_trusted_proxy": True,
        "source": "flask",
        "method": "GET",
        "headers": {
            "HEADER_1": ["header 1 value"],
            "HEADER_2": ["Header 2 value"],
            "COOKIE": ["sessionId=abc123xyz456;"],
            "HOST": ["localhost:8080"],
            "CONTENT_TYPE": ["application/json"],
            "USER_AGENT": ["Mozilla/5.0"],
        },
        "cookies": {"sessionId": "abc123xyz456"},
        "url": "http://localhost:8080/hello",
        "query": {"user": ["JohnDoe"], "age": ["30", "35"]},
        "body": {"test": True},
        "route": "/hello",
        "subdomains": [],
        "user": None,
        "rate_limit_group": None,
        "remote_address": "198.51.100.23",
        "parsed_userinput": {},
        "xml": {},
        "outgoing_req_redirects": [],
        "executed_middleware": False,
        "tracked_events": 0,
        "tracked_events_limit_warning_logged": False,
        "route_params": [],
        "protection_forced_off": None,
    }
    assert context.get_user_agent() == "Mozilla/5.0"


@pytest.mark.parametrize("source", ["flask", "starlette"])
@pytest.mark.parametrize(
    "setting, peer, trusted, client_ip",
    [
        ("1.2.3.0/24", "1.2.3.4", True, "9.9.9.9"),
        ("1.2.3.0/24", "8.8.8.8", False, "8.8.8.8"),
        ("false", "1.2.3.4", False, "1.2.3.4"),
        ("2", "1.2.3.4", True, "9.9.9.9"),
    ],
)
def test_proxy_trust_in_request_context(
    monkeypatch, source, setting, peer, trusted, client_ip
):
    from aikido_zen.vulnerabilities.ssrf.find_hostname_in_context import (
        find_hostname_in_context,
    )

    monkeypatch.setenv("AIKIDO_TRUST_PROXY", setting)
    if source == "flask":
        request = dict(basic_wsgi_req)
        request["REMOTE_ADDR"] = peer
        request["HTTP_X_FORWARDED_FOR"] = "9.9.9.9, 1.2.3.5"
    else:
        request = {
            "method": "GET",
            "headers": [
                (b"host", b"localhost:8080"),
                (b"x-forwarded-for", b"9.9.9.9, 1.2.3.5"),
            ],
            "query_string": b"",
            "client": (peer, 1234),
            "server": ("localhost", 8080),
            "scheme": "http",
            "root_path": "",
            "path": "/hello",
        }
    context = Context(req=request, body={"url": "http://localhost:8080"}, source=source)
    assert context.remote_address == client_ip
    assert context.is_behind_trusted_proxy is trusted
    assert (find_hostname_in_context("localhost", context, 8080) is None) is trusted
    restored = pickle.loads(pickle.dumps(context))
    assert restored.is_behind_trusted_proxy is trusted


def test_set_as_current_context(mocker):
    # Test set_as_current_context() method
    context = Context(req=basic_wsgi_req, body=12, source="flask")
    context.set_as_current_context()
    assert get_current_context() == context


def test_get_current_context_with_context(mocker):
    # Test get_current_context() when a context is set
    context = Context(req=basic_wsgi_req, body=456, source="flask")
    context.set_as_current_context()
    assert get_current_context() == context


def test_context_is_picklable(mocker):
    context = Context(req=basic_wsgi_req, body=123, source="flask")
    pickled_obj = pickle.dumps(context)
    unpickled_obj = pickle.loads(pickled_obj)
    assert unpickled_obj.source == "flask"
    assert unpickled_obj.method == "GET"
    assert unpickled_obj.remote_address == "198.51.100.23"
    assert unpickled_obj.is_behind_trusted_proxy is True
    assert unpickled_obj.url == "http://localhost:8080/hello"
    assert unpickled_obj.body == 123
    assert unpickled_obj.headers == {
        "HEADER_1": ["header 1 value"],
        "HEADER_2": ["Header 2 value"],
        "COOKIE": ["sessionId=abc123xyz456;"],
        "HOST": ["localhost:8080"],
        "CONTENT_TYPE": ["application/json"],
        "USER_AGENT": ["Mozilla/5.0"],
    }
    assert unpickled_obj.query == {"user": ["JohnDoe"], "age": ["30", "35"]}
    assert unpickled_obj.cookies == {"sessionId": "abc123xyz456"}


def test_set_valid_dict():
    valid_body = {"key": "value"}
    context = Context(req=basic_wsgi_req, body=valid_body, source="flask")
    assert context.body == valid_body


def test_set_valid_list():
    valid_body = [1, 2, 3]
    context = Context(req=basic_wsgi_req, body=valid_body, source="flask")
    assert context.body == valid_body


def test_set_valid_string():
    valid_body = "This is a valid string"
    context = Context(req=basic_wsgi_req, body=valid_body, source="flask")
    assert context.body == valid_body


def test_set_empty_byte_string():
    invalid_body = b""
    context = Context(req=basic_wsgi_req, body=invalid_body, source="flask")
    assert context.body is None


def test_set_normal_byte_string():
    body = b"Hello World!"
    context = Context(req=basic_wsgi_req, body=body, source="flask")
    assert context.body == "Hello World!"


def test_set_byte_string_wrong_encoding():
    body = "hello world! 😊".encode("utf-16")  # UTF-16 bytes are not valid UTF-8
    context = Context(req=basic_wsgi_req, body=body, source="flask")
    # Invalid bytes are replaced with � so the body is still scannable.
    assert context.body == body.decode("utf-8", errors="replace")


def test_set_none():
    context = Context(req=basic_wsgi_req, body=None, source="flask")
    assert context.body is None


def test_set_valid_nested_json_string():
    context = Context(req=basic_wsgi_req, body=None, source="flask")
    context.set_body('{"key": {"nested_key": "nested_value"}}')
    assert context.body == {"key": {"nested_key": "nested_value"}}


def test_set_invalid_json_with_unmatched_quotes():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body('{"key": "value\'s}')
    assert context.body == '{"key": "value\'s}'  # Should remain as string


def test_set_valid_json_with_array():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body('{"key": [1, 2, 3]}')
    assert context.body == {"key": [1, 2, 3]}


def test_set_valid_json_with_spaces():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body('               {"key": [1, 2, 3]}         ')
    assert context.body == {"key": [1, 2, 3]}


def test_valid_json_string_with_newlines():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body('\r\n\r\n"hello"\r\n\r\n')
    assert context.body == "hello"


def test_valid_json_string_with_spaces():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body('"                    hello              "')
    assert context.body == "                    hello              "


def test_set_valid_json_with_newlines():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body('\r\n\r\n{"key": [1, 2, 3]}\r\n\r\n')
    assert context.body == {"key": [1, 2, 3]}


def test_set_valid_json_with_spaces_and_array():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body("               [1, 2, 3]         ")
    assert context.body == [1, 2, 3]
    context.set_body("               (1, 2, 3)         ")
    assert context.body == "               (1, 2, 3)         "


def test_set_valid_json_with_spaces_and_array_bytes():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body(b"               [1, 2, 3]         ")
    assert context.body == [1, 2, 3]
    context.set_body(b"               (1, 2, 3)         ")
    assert context.body == "               (1, 2, 3)         "


def test_set_valid_json_with_complex_array():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body(
        '               [{"hello": "world", "one": 123}, 2, "hiya"]         '
    )
    assert context.body == [{"hello": "world", "one": 123}, 2, "hiya"]


def test_set_valid_json_with_complex_array_bytes():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body(
        b'               [{"hello": "world", "one": 123}, 2, "hiya"]         '
    )
    assert context.body == [{"hello": "world", "one": 123}, 2, "hiya"]


def test_empty_string_becomes_none():
    context = Context(req=basic_wsgi_req, body=None, source="flask")

    context.set_body("")
    assert context.body is None


def test_set_valid_json_with_special_characters():
    context = Context(req=basic_wsgi_req, body=None, source="flask")
    context.set_body('{"key": "value with special characters !@#$%^&*()"}')
    assert context.body == {"key": "value with special characters !@#$%^&*()"}


def test_set_valid_json_with_special_characters_bytes():
    context = Context(req=basic_wsgi_req, body=None, source="flask")
    context.set_body(b'{"key": "value with special characters !@#$%^&*()"}')
    assert context.body == {"key": "value with special characters !@#$%^&*()"}


def test_set_protection_forced_off():
    context = Context(req=basic_wsgi_req, body=None, source="flask")
    context.set_force_protection_off(True)
    assert context.protection_forced_off is True
    context.set_force_protection_off(False)
    assert context.protection_forced_off is False
    context.set_force_protection_off(None)
    assert context.protection_forced_off is None


def test_set_bytes_with_invalid_utf8_prefix():
    # Regression: AIKIDO-5RDTZW1V — a single invalid UTF-8 byte (e.g. \xff) prepended
    # to a path traversal payload must not bypass detection.  The body must be decoded
    # with errors="replace" so the traversal string remains visible to sinks.
    body = b"\xff/../../../../../etc/passwd"
    context = Context(req=basic_wsgi_req, body=body, source="flask")
    assert isinstance(context.body, str)
    assert "/../../../../../etc/passwd" in context.body


def test_set_bytes_json_with_surrogate_bytes():
    # Regression: AIKIDO-B3YABOSP — surrogate bytes embedded in a JSON body must not
    # bypass detection.  json.loads(bytes) uses surrogatepass internally, so the dict
    # is parsed and the attack payload (e.g. {"$regex": ".*"}) is visible.
    body = b'{"username": {"$regex": ".*"}, "bypass": "\xed\xa0\x80"}'
    context = Context(req=basic_wsgi_req, body=body, source="flask")
    assert isinstance(context.body, dict)
    assert context.body.get("username") == {"$regex": ".*"}


@pytest.mark.parametrize("opening", [b"[", b'{"a":'], ids=["list", "object"])
def test_set_bytes_with_json_prefix_too_deep_to_parse(opening):
    body = opening * LEVELS_TOO_DEEP_TO_PARSE + b"1' OR 1=1 -- "
    context = Context(req=basic_wsgi_req, body=body, source="flask")
    assert isinstance(context.body, str)
    assert context.body.endswith("1' OR 1=1 -- ")
