import pytest
from .is_web_scanner import is_web_scanner


class Context:
    def __init__(self, route, method, query):
        self.remote_address = "::1"
        self.method = method
        self.url = "http://example.com"
        self.query = query
        self.headers = {}
        self.body = {}
        self.cookies = {}
        self.route_params = {}
        self.source = "flask"
        self.route = route
        self.parsed_userinput = {}


def get_test_context(path="/", method="GET", query=None):
    return Context(path, method, query)


def test_is_web_scanner():
    assert is_web_scanner(get_test_context("/wp-config.php", "GET"))
    assert is_web_scanner(get_test_context("/.env", "GET"))
    assert is_web_scanner(get_test_context("/test/.env.bak", "GET"))
    assert is_web_scanner(get_test_context("/.git/config", "GET"))
    assert is_web_scanner(get_test_context("/.aws/config", "GET"))
    assert is_web_scanner(get_test_context("/../secret", "GET"))
    assert is_web_scanner(get_test_context("/", "BADMETHOD"))
    assert is_web_scanner(get_test_context("/", "GET", {"test": "SELECT * FROM admin"}))
    assert is_web_scanner(get_test_context("/", "GET", {"test": "../etc/passwd"}))


def test_is_not_web_scanner():
    assert not is_web_scanner(get_test_context("graphql", "POST"))
    assert not is_web_scanner(get_test_context("/api/v1/users", "GET"))
    assert not is_web_scanner(get_test_context("/public/index.html", "GET"))
    assert not is_web_scanner(get_test_context("/static/js/app.js", "GET"))
    assert not is_web_scanner(get_test_context("/uploads/image.png", "GET"))
    assert not is_web_scanner(get_test_context("/", "GET", {"test": "1'"}))
    assert not is_web_scanner(get_test_context("/", "GET", {"test": "abcd"}))
