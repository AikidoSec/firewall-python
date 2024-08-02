import pytest
from .try_parse_url import try_parse_url


def test_valid_http_url():
    url = "http://example.com"
    result = try_parse_url(url)
    assert result is not None
    assert result.scheme == "http"
    assert result.netloc == "example.com"


def test_valid_https_url():
    url = "https://example.com/path?query=1"
    result = try_parse_url(url)
    assert result is not None
    assert result.scheme == "https"
    assert result.netloc == "example.com"
    assert result.path == "/path"
    assert result.query == "query=1"


def test_invalid_url_missing_scheme():
    url = "example.com/path"
    result = try_parse_url(url)
    assert result is None


def test_invalid_url_missing_netloc():
    url = "http:///path"
    result = try_parse_url(url)
    assert result is None


def test_invalid_url():
    url = "ht!tp://example.com"
    result = try_parse_url(url)
    assert result is None


def test_empty_url():
    url = ""
    result = try_parse_url(url)
    assert result is None


def test_url_with_only_scheme():
    url = "http://"
    result = try_parse_url(url)
    assert result is None


def test_url_with_special_characters():
    url = "http://example.com/path?query=1&other=value#fragment"
    result = try_parse_url(url)
    assert result is not None
    assert result.scheme == "http"
    assert result.netloc == "example.com"
    assert result.path == "/path"
    assert result.query == "query=1&other=value"
    assert result.fragment == "fragment"
