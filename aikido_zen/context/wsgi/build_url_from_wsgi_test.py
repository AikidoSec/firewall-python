import pytest
from .build_url_from_wsgi import build_url_from_wsgi


def test_build_url_from_wsgi_http():
    request = {
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "example.com",
        "PATH_INFO": "/path/to/resource",
    }
    expected = "http://example.com/path/to/resource"
    assert build_url_from_wsgi(request) == expected


def test_build_url_from_wsgi_https():
    request = {
        "wsgi.url_scheme": "https",
        "HTTP_HOST": "example.com",
        "PATH_INFO": "/secure/resource",
    }
    expected = "https://example.com/secure/resource"
    assert build_url_from_wsgi(request) == expected


def test_build_url_from_wsgi_with_missing_hostname():
    request = {
        "wsgi.url_scheme": "https",
        "SERVER_NAME": "127.0.0.1",
        "SERVER_PORT": 1337,
        "PATH_INFO": "/secure/resource",
    }
    expected = "https://127.0.0.1:1337/secure/resource"
    assert build_url_from_wsgi(request) == expected


def test_build_url_from_wsgi_with_empty_hostname():
    request = {
        "wsgi.url_scheme": "https",
        "HTTP_HOST": "",
        "SERVER_NAME": "127.0.0.1",
        "SERVER_PORT": 1337,
        "PATH_INFO": "/secure/resource",
    }
    expected = "https://127.0.0.1:1337/secure/resource"
    assert build_url_from_wsgi(request) == expected


def test_build_url_from_wsgi_with_query_string():
    request = {
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "example.com",
        "PATH_INFO": "/search",
        "QUERY_STRING": "q=test",
    }
    # Note: The function does not currently handle query strings, so we won't include it in the expected output
    expected = "http://example.com/search"
    assert build_url_from_wsgi(request) == expected


def test_build_url_from_wsgi_root_path():
    request = {"wsgi.url_scheme": "http", "HTTP_HOST": "example.com", "PATH_INFO": "/"}
    expected = "http://example.com/"
    assert build_url_from_wsgi(request) == expected


def test_build_url_from_wsgi_empty_path():
    request = {"wsgi.url_scheme": "http", "HTTP_HOST": "example.com", "PATH_INFO": ""}
    expected = "http://example.com"
    assert build_url_from_wsgi(request) == expected


def test_build_url_from_wsgi_missing_host():
    request = {"wsgi.url_scheme": "http", "PATH_INFO": "/path/to/resource"}
    with pytest.raises(KeyError):
        build_url_from_wsgi(request)


def test_build_url_from_wsgi_missing_scheme():
    request = {"HTTP_HOST": "example.com", "PATH_INFO": "/path/to/resource"}
    with pytest.raises(KeyError):
        build_url_from_wsgi(request)
