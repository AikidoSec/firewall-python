import pytest
from .normalize_asgi_headers import normalize_asgi_headers


def test_normalize_asgi_headers_basic():
    headers = [
        (b"content-type", b"text/html"),
        (b"accept-encoding", b"gzip, deflate"),
    ]
    expected = {"CONTENT_TYPE": "text/html", "ACCEPT_ENCODING": "gzip, deflate"}
    assert normalize_asgi_headers(headers) == expected


def test_normalize_asgi_headers_empty():
    headers = []
    expected = {}
    assert normalize_asgi_headers(headers) == expected


def test_normalize_asgi_headers_with_special_characters():
    headers = [
        (b"content-type", b"text/html"),
        (b"x-custom-header", b"some_value"),
        (b"accept-encoding", b"gzip, deflate"),
    ]
    expected = {
        "CONTENT_TYPE": "text/html",
        "X_CUSTOM_HEADER": "some_value",
        "ACCEPT_ENCODING": "gzip, deflate",
    }
    assert normalize_asgi_headers(headers) == expected


def test_normalize_asgi_headers_with_dashes():
    headers = [
        (b"X-Forwarded-For", b"192.168.1.1"),
        (b"X-Request-ID", b"abc123"),
    ]
    expected = {"X_FORWARDED_FOR": "192.168.1.1", "X_REQUEST_ID": "abc123"}
    assert normalize_asgi_headers(headers) == expected


def test_normalize_asgi_headers_case_insensitivity():
    headers = [
        (b"Content-Type", b"text/html"),
        (b"ACCEPT-ENCODING", b"gzip, deflate"),
    ]
    expected = {"CONTENT_TYPE": "text/html", "ACCEPT_ENCODING": "gzip, deflate"}
    assert normalize_asgi_headers(headers) == expected


def test_normalize_asgi_headers_unicode():
    headers = [
        (b"content-type", b"text/html"),
        (b"custom-header", b"value"),
    ]
    expected = {"CONTENT_TYPE": "text/html", "CUSTOM_HEADER": "value"}
    assert normalize_asgi_headers(headers) == expected


def test_normalize_asgi_headers_mixed_case_and_dashes():
    headers = [
        (b"Content-Type", b"text/html"),
        (b"X-Custom-Header", b"some_value"),
        (b"Accept-Encoding", b"gzip, deflate"),
    ]
    expected = {
        "CONTENT_TYPE": "text/html",
        "X_CUSTOM_HEADER": "some_value",
        "ACCEPT_ENCODING": "gzip, deflate",
    }
    assert normalize_asgi_headers(headers) == expected


def test_normalize_asgi_headers_non_ascii():
    headers = [
        (b"content-type", b"text/html"),
        (b"custom-header", b"value"),
        (b"X-Header-With-Emoji", b"test"),
    ]
    expected = {
        "CONTENT_TYPE": "text/html",
        "CUSTOM_HEADER": "value",
        "X_HEADER_WITH_EMOJI": "test",
    }
    assert normalize_asgi_headers(headers) == expected


def test_normalize_asgi_headers_large_input():
    headers = [
        (f"header-{i}".encode("utf-8"), f"value-{i}".encode("utf-8"))
        for i in range(1000)
    ]
    expected = {f"HEADER_{i}": f"value-{i}" for i in range(1000)}
    assert normalize_asgi_headers(headers) == expected
