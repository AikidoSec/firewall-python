import pytest
from aikido_zen.context.asgi import set_asgi_attributes_on_context


class Context:
    def __init__(self):
        self.headers = None
        self.cookies = None
        self.method = None
        self.url = None
        self.query = None
        self.remote_address = None


# Scope 1 :
TEST_ASGI_SCOPE_1 = {
    "method": "PUT",
    "headers": [(b"COOKIE", b"a=b; c=d"), (b"header1_test-2", b"testValue2198&")],
    "query_string": b"a=b&b=d",
    "client": ["1.1.1.1"],
    "server": ["192.168.0.1", 443],
    "scheme": "https",
    "root_path": "192.168.0.1",
    "path": "192.168.0.1/a/b/c/d",
}


def test_asgi_scope_1():
    context1 = Context()
    set_asgi_attributes_on_context(context1, TEST_ASGI_SCOPE_1)
    assert context1.method == "PUT"
    assert context1.remote_address == "1.1.1.1"
    assert context1.query == {"a": ["b"], "b": ["d"]}
    assert context1.headers == {
        "COOKIE": "a=b; c=d",
        "HEADER1_TEST_2": "testValue2198&",
    }
    assert context1.cookies == {"a": "b", "c": "d"}
    assert context1.url == "https://192.168.0.1:443/a/b/c/d"


# Scope 2 :
TEST_ASGI_SCOPE_2 = {
    "method": "GET",
    "headers": [(b"COOKIE", b"x=y; z=w"), (b"header2_test-1", b"anotherValue")],
    "query_string": b"x=y&z=w",
    "client": ["2.2.2.2"],
    "server": ["192.168.0.2", 80],
    "scheme": "http",
    "root_path": "",
    "path": "/path/to/resource",
}


def test_asgi_scope_2():
    context2 = Context()
    set_asgi_attributes_on_context(context2, TEST_ASGI_SCOPE_2)
    assert context2.method == "GET"
    assert context2.remote_address == "2.2.2.2"
    assert context2.query == {"x": ["y"], "z": ["w"]}
    assert context2.headers == {
        "COOKIE": "x=y; z=w",
        "HEADER2_TEST_1": "anotherValue",
    }
    assert context2.cookies == {"x": "y", "z": "w"}
    assert context2.url == "http://192.168.0.2:80/path/to/resource"


# Scope 3 :
TEST_ASGI_SCOPE_3 = {
    "method": "POST",
    "headers": [(b"COOKIE", b"session=abc123"), (b"header3_test-3", b"postValue")],
    "query_string": b"key1=value1&key2=value2",
    "client": ["3.3.3.3"],
    "server": ["192.168.0.3", 8080],
    "scheme": "http",
    "root_path": "/api",
    "path": "/api/v1/resource",
}


def test_asgi_scope_3():
    context3 = Context()
    set_asgi_attributes_on_context(context3, TEST_ASGI_SCOPE_3)
    assert context3.method == "POST"
    assert context3.remote_address == "3.3.3.3"
    assert context3.query == {"key1": ["value1"], "key2": ["value2"]}
    assert context3.headers == {
        "COOKIE": "session=abc123",
        "HEADER3_TEST_3": "postValue",
    }
    assert context3.cookies == {"session": "abc123"}
    assert context3.url == "http://192.168.0.3:8080/v1/resource"


# Scope 4 :
TEST_ASGI_SCOPE_4 = {
    "method": "DELETE",
    "headers": [(b"header4_test-4", b"deleteValue")],
    "query_string": b"",
    "client": ["4.4.4.4"],
    "server": ["192.168.0.4", 443],
    "scheme": "https",
    "root_path": "/secure",
    "path": "/secure/resource/123",
}


def test_asgi_scope_4():
    context4 = Context()
    set_asgi_attributes_on_context(context4, TEST_ASGI_SCOPE_4)
    assert context4.method == "DELETE"
    assert context4.remote_address == "4.4.4.4"
    assert context4.query == {}
    assert context4.headers == {
        "HEADER4_TEST_4": "deleteValue",
    }
    assert context4.cookies == {}  # No cookies in this scope
    assert context4.url == "https://192.168.0.4:443/resource/123"
