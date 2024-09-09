import pytest
from .normalize_url import normalize_url


def test_normalize_url():
    # Test with standard URLs
    assert normalize_url("http://example.com") == "http://example.com"
    assert normalize_url("https://example.com") == "https://example.com"
    assert normalize_url("http://example.com/") == "http://example.com"
    assert normalize_url("http://example.com/path/") == "http://example.com/path"
    assert normalize_url("http://example.com/path") == "http://example.com/path"

    # Test with lowercase and uppercase schemes
    assert normalize_url("HTTP://EXAMPLE.COM") == "http://example.com"
    assert normalize_url("Https://EXAMPLE.COM") == "https://example.com"

    # Test with default ports
    assert normalize_url("http://example.com:80/path") == "http://example.com/path"
    assert normalize_url("https://example.com:443/path") == "https://example.com/path"

    # Test with non-default ports
    assert (
        normalize_url("http://example.com:8080/path") == "http://example.com:8080/path"
    )
    assert (
        normalize_url("https://example.com:8443/path")
        == "https://example.com:8443/path"
    )

    # Test with query parameters
    assert (
        normalize_url("http://example.com/path?query=1")
        == "http://example.com/path?query=1"
    )
    assert (
        normalize_url("http://example.com/path/?query=1")
        == "http://example.com/path?query=1"
    )

    # Test with fragments
    assert (
        normalize_url("http://example.com/path#fragment")
        == "http://example.com/path#fragment"
    )
    assert (
        normalize_url("http://example.com/path/?query=1#fragment")
        == "http://example.com/path?query=1#fragment"
    )

    # Test with URLs that have trailing slashes and mixed cases
    assert normalize_url("http://Example.com/Path/") == "http://example.com/Path"
    assert (
        normalize_url("http://example.com/path/another/")
        == "http://example.com/path/another"
    )

    # Test with empty URL
    assert normalize_url("") == ""
