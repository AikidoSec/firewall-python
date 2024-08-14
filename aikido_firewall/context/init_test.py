import pytest
import pickle
import json
from aikido_firewall.context import Context, get_current_context


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
    wsgi_raw_body = "dog_name=Doggo 1&test=Test 1"
    context = Context(req=wsgi_request, raw_body=wsgi_raw_body, source="django")
    assert context.__dict__ == {
        "source": "django",
        "method": "POST",
        "headers": {
            "HEADER_1": "header 1 value",
            "HEADER_2": "Header 2 value",
            "COOKIE": "sessionId=abc123xyz456;",
            "HOST": "example.com",
        },
        "cookies": {"sessionId": "abc123xyz456"},
        "url": "https://example.com/hello",
        "query": {"user": ["JohnDoe"], "age": ["30", "35"]},
        "body": {"dog_name": ["Doggo 1"], "test": ["Test 1"]},
        "route": "/hello",
        "subdomains": [],
        "user": None,
        "remote_address": "198.51.100.23",
        "parsed_userinput": {},
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
    wsgi_raw_body = '{"a": 23, "b": 45, "Hello": [1, 2, 3]}'
    context = Context(req=wsgi_request, raw_body=wsgi_raw_body, source="flask")
    assert context.__dict__ == {
        "source": "flask",
        "method": "GET",
        "headers": {
            "HEADER_1": "header 1 value",
            "HEADER_2": "Header 2 value",
            "COOKIE": "sessionId=abc123xyz456;",
            "HOST": "localhost:8080",
        },
        "cookies": {"sessionId": "abc123xyz456"},
        "url": "http://localhost:8080/hello",
        "query": {"user": ["JohnDoe"], "age": ["30", "35"]},
        "body": {"a": 23, "b": 45, "Hello": [1, 2, 3]},
        "route": "/hello",
        "subdomains": [],
        "user": None,
        "remote_address": "198.51.100.23",
        "parsed_userinput": {},
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
    wsgi_raw_body = '{"a": 23, "b": 45, "Hello": [1, 2, 3]}'
    context = Context(req=wsgi_request, raw_body=wsgi_raw_body, source="flask")
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
    wsgi_raw_body = '{"a": 23, "b": 45, "Hello": [1, 2, 3]}'
    context = Context(req=wsgi_request, raw_body=wsgi_raw_body, source="flask")
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
    wsgi_raw_body = '{"a": 23, "b": 45, "Hello": [1, 2, 3]}'
    context = Context(req=wsgi_request, raw_body=wsgi_raw_body, source="flask")
    pickled_obj = pickle.dumps(context)
    unpickled_obj = pickle.loads(pickled_obj)
    assert unpickled_obj.source == "flask"
    assert unpickled_obj.method == "GET"
    assert unpickled_obj.remote_address == "198.51.100.23"
    assert unpickled_obj.url == "http://localhost:8080/hello"
    assert unpickled_obj.body == {"a": 23, "b": 45, "Hello": [1, 2, 3]}
    assert unpickled_obj.headers == {
        "HEADER_1": "header 1 value",
        "HEADER_2": "Header 2 value",
        "COOKIE": "sessionId=abc123xyz456;",
        "HOST": "localhost:8080",
    }
    assert unpickled_obj.query == {"user": ["JohnDoe"], "age": ["30", "35"]}
    assert unpickled_obj.cookies == {"sessionId": "abc123xyz456"}
