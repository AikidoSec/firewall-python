import pytest

from .build_url_from_asgi import build_url_from_asgi


def test_build_url_from_asgi_http():
    scope = {
        "scheme": "http",
        "server": ("localhost", 8000),
        "root_path": "",
        "path": "/api/v1/resource",
    }
    expected = "http://localhost:8000/api/v1/resource"
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_https():
    scope = {
        "scheme": "https",
        "server": ("example.com", 443),
        "root_path": "",
        "path": "/secure/resource",
    }
    expected = "https://example.com:443/secure/resource"
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_with_root_path():
    scope = {
        "scheme": "http",
        "server": ("localhost", 8000),
        "root_path": "/api",
        "path": "/api/v1/resource",
    }
    expected = "http://localhost:8000/v1/resource"
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_with_empty_path():
    scope = {
        "scheme": "http",
        "server": ("localhost", 8000),
        "root_path": "",
        "path": "",
    }
    expected = "http://localhost:8000"
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_without_server():
    scope = {
        "scheme": "http",
        "server": None,
        "root_path": "",
        "path": "/api/v1/resource",
    }
    expected = None
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_with_no_root_path():
    scope = {
        "scheme": "http",
        "server": ("localhost", 8000),
        "path": "/api/v1/resource",
    }
    expected = "http://localhost:8000/api/v1/resource"
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_with_port_80():
    scope = {
        "scheme": "http",
        "server": ("localhost", 80),
        "root_path": "",
        "path": "/",
    }
    expected = "http://localhost:80/"
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_with_port_443():
    scope = {
        "scheme": "https",
        "server": ("localhost", 443),
        "root_path": "",
        "path": "/",
    }
    expected = "https://localhost:443/"
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_with_trailing_slash_in_root_path():
    scope = {
        "scheme": "http",
        "server": ("localhost", 8000),
        "root_path": "/api",
        "path": "/api/v1/resource",
    }
    expected = "http://localhost:8000/v1/resource"
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_with_multiple_slashes():
    scope = {
        "scheme": "http",
        "server": ("localhost", 8000),
        "root_path": "/api/",
        "path": "/api//v1/resource",
    }
    expected = "http://localhost:8000/v1/resource"
    assert build_url_from_asgi(scope) == expected


def test_build_url_from_asgi_with_query_string():
    scope = {
        "scheme": "http",
        "server": ("localhost", 8000),
        "root_path": "",
        "path": "/api/v1/resource?query=1",
    }
    expected = "http://localhost:8000/api/v1/resource?query=1"
    assert build_url_from_asgi(scope) == expected
