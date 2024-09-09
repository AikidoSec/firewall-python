import pytest
from .extract_wsgi_headers import extract_wsgi_headers


def test_extract_wsgi_headers_single_header():
    request = {"REQUEST_METHOD": "GET", "HTTP_USER_AGENT": "Mozilla/5.0"}
    expected = {"USER_AGENT": "Mozilla/5.0"}
    assert extract_wsgi_headers(request) == expected


def test_extract_wsgi_headers_multiple_headers():
    request = {
        "REQUEST_METHOD": "POST",
        "HTTP_HOST": "example.com",
        "HTTP_ACCEPT": "text/html",
        "HTTP_CONTENT_TYPE": "application/json",
    }
    expected = {
        "HOST": "example.com",
        "ACCEPT": "text/html",
        "CONTENT_TYPE": "application/json",
    }
    assert extract_wsgi_headers(request) == expected


def test_extract_wsgi_headers_no_http_headers():
    request = {"REQUEST_METHOD": "GET", "REMOTE_ADDR": "192.168.1.1"}
    expected = {}
    assert extract_wsgi_headers(request) == expected


def test_extract_wsgi_headers_empty_request():
    request = {}
    expected = {}
    assert extract_wsgi_headers(request) == expected


def test_extract_wsgi_headers_mixed_headers():
    request = {
        "REQUEST_METHOD": "GET",
        "HTTP_USER_AGENT": "Mozilla/5.0",
        "HTTP_ACCEPT_LANGUAGE": "en-US,en;q=0.5",
        "OTHER_HEADER": "value",
    }
    expected = {"USER_AGENT": "Mozilla/5.0", "ACCEPT_LANGUAGE": "en-US,en;q=0.5"}
    assert extract_wsgi_headers(request) == expected
