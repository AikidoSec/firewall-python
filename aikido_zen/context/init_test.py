import pytest
import pickle
import json
from aikido_zen.context import Context, get_current_context, current_context


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
        "source": "django",
        "method": "POST",
        "headers": {
            "HEADER_1": "header 1 value",
            "HEADER_2": "Header 2 value",
            "COOKIE": "sessionId=abc123xyz456;",
            "HOST": "example.com",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
        },
        "cookies": {"sessionId": "abc123xyz456"},
        "url": "https://example.com/hello",
        "query": {"user": ["JohnDoe"], "age": ["30", "35"]},
        "body": 123,
        "route": "/hello",
        "subdomains": [],
        "user": None,
        "remote_address": "198.51.100.23",
        "parsed_userinput": {},
        "xml": {},
        "outgoing_req_redirects": [],
    }


def test_wsgi_context_2():
    wsgi_request = {
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
    }
    context = Context(req=wsgi_request, body={"test": True}, source="flask")
    assert context.__dict__ == {
        "source": "flask",
        "method": "GET",
        "headers": {
            "HEADER_1": "header 1 value",
            "HEADER_2": "Header 2 value",
            "COOKIE": "sessionId=abc123xyz456;",
            "HOST": "localhost:8080",
            "CONTENT_TYPE": "application/json",
        },
        "cookies": {"sessionId": "abc123xyz456"},
        "url": "http://localhost:8080/hello",
        "query": {"user": ["JohnDoe"], "age": ["30", "35"]},
        "body": {"test": True},
        "route": "/hello",
        "subdomains": [],
        "user": None,
        "remote_address": "198.51.100.23",
        "parsed_userinput": {},
        "xml": {},
        "outgoing_req_redirects": [],
    }


def test_set_as_current_context(mocker):
    # Test set_as_current_context() method
    wsgi_request = {
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
    }
    context = Context(req=wsgi_request, body=12, source="flask")
    context.set_as_current_context()
    assert get_current_context() == context


def test_get_current_context_with_context(mocker):
    # Test get_current_context() when a context is set
    wsgi_request = {
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
    }
    context = Context(req=wsgi_request, body=456, source="flask")
    context.set_as_current_context()
    assert get_current_context() == context


def test_context_is_picklable(mocker):
    wsgi_request = {
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
    }
    context = Context(req=wsgi_request, body=123, source="flask")
    pickled_obj = pickle.dumps(context)
    unpickled_obj = pickle.loads(pickled_obj)
    assert unpickled_obj.source == "flask"
    assert unpickled_obj.method == "GET"
    assert unpickled_obj.remote_address == "198.51.100.23"
    assert unpickled_obj.url == "http://localhost:8080/hello"
    assert unpickled_obj.body == 123
    assert unpickled_obj.headers == {
        "HEADER_1": "header 1 value",
        "HEADER_2": "Header 2 value",
        "COOKIE": "sessionId=abc123xyz456;",
        "HOST": "localhost:8080",
        "CONTENT_TYPE": "application/json",
    }
    assert unpickled_obj.query == {"user": ["JohnDoe"], "age": ["30", "35"]}
    assert unpickled_obj.cookies == {"sessionId": "abc123xyz456"}
