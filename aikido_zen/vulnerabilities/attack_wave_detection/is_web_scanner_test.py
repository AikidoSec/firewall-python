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
    assert is_web_scanner(get_test_context("/wp-config.php", "GET"), 404)
    assert is_web_scanner(get_test_context("/.env", "GET"), 404)
    assert is_web_scanner(get_test_context("/test/.env.bak", "GET"), 404)
    assert is_web_scanner(get_test_context("/.git/config", "GET"), 404)
    assert is_web_scanner(get_test_context("/.aws/config", "GET"), 404)
    assert is_web_scanner(get_test_context("/../secret", "GET"), 404)
    assert is_web_scanner(get_test_context("/", "BADMETHOD"), 404)
    assert is_web_scanner(get_test_context("/", "GET", {"test": "SELECT * FROM admin"}), 404)
    assert is_web_scanner(get_test_context("/", "GET", {"test": "../etc/passwd"}), 404)


def test_is_not_web_scanner():
    assert not is_web_scanner(get_test_context("graphql", "POST"), 404)
    assert not is_web_scanner(get_test_context("/api/v1/users", "GET"), 404)
    assert not is_web_scanner(get_test_context("/public/index.html", "GET"), 404)
    assert not is_web_scanner(get_test_context("/static/js/app.js", "GET"), 404)
    assert not is_web_scanner(get_test_context("/uploads/image.png", "GET"), 404)
    assert not is_web_scanner(get_test_context("/", "GET", {"test": "1'"}), 404)
    assert not is_web_scanner(get_test_context("/", "GET", {"test": "abcd"}), 404)


def test_foreign_extension_only_on_404():
    assert is_web_scanner(get_test_context("/admin.php", "GET"), 404)
    assert not is_web_scanner(get_test_context("/admin.php", "GET"), 200)
    assert not is_web_scanner(get_test_context("/admin.php", "GET"), 301)
    assert is_web_scanner(get_test_context("/app.jsp", "GET"), 404)
    assert not is_web_scanner(get_test_context("/app.jsp", "GET"), 200)
