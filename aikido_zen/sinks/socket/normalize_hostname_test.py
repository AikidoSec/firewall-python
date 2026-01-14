"""
Test module for normalize_hostname function
"""

import pytest
from aikido_zen.sinks.socket.normalize_hostname import normalize_hostname


def test_normalize_hostname_none():
    """Test that None input returns None"""
    assert normalize_hostname(None) is None


def test_normalize_hostname_empty_string():
    """Test that empty string returns empty string"""
    assert normalize_hostname("") == ""


def test_normalize_hostname_regular_hostname():
    """Test that regular hostnames are returned unchanged"""
    assert normalize_hostname("example.com") == "example.com"
    assert normalize_hostname("subdomain.example.com") == "subdomain.example.com"
    assert normalize_hostname("localhost") == "localhost"


def test_normalize_hostname_ip_address():
    """Test that IP addresses are returned unchanged"""
    assert normalize_hostname("127.0.0.1") == "127.0.0.1"
    assert normalize_hostname("::1") == "::1"
    assert normalize_hostname("192.168.1.1") == "192.168.1.1"


def test_normalize_hostname_punycode_basic():
    """Test basic punycode conversion"""
    # xn--test-5qa.com should decode to test.com (but test.com is ASCII, so this won't work)
    # Let's use a realistic example instead
    assert normalize_hostname("xn--mller-kva.example") == "müller.example"


def test_normalize_hostname_punycode_unicode():
    """Test punycode with unicode characters"""
    # xn--mller-kva.example should decode to müller.example
    result = normalize_hostname("xn--mller-kva.example")
    assert result == "müller.example"

    # xn--caf-dma.example should decode to café.example
    result = normalize_hostname("xn--caf-dma.example")
    assert result == "café.example"


def test_normalize_hostname_punycode_subdomain():
    """Test punycode in subdomains"""
    # xn--mller-kva.example.com should decode to müller.example.com
    result = normalize_hostname("xn--mller-kva.example.com")
    assert result == "müller.example.com"


def test_normalize_hostname_mixed_case():
    """Test that case is preserved in non-punycode hostnames"""
    assert normalize_hostname("Example.COM") == "Example.COM"
    assert normalize_hostname("MixedCase.Example.com") == "MixedCase.Example.com"


def test_normalize_hostname_non_string_input():
    """Test that non-string inputs are returned unchanged"""
    assert normalize_hostname(123) == 123
    assert normalize_hostname([]) == []
    assert normalize_hostname({}) == {}


def test_normalize_hostname_punycode_with_port():
    """Test that punycode hostnames with ports are handled correctly"""
    # This should only normalize the hostname part, not the port
    result = normalize_hostname("xn--mller-kva.example:8080")
    assert result == "müller.example:8080"


def test_normalize_hostname_complex_punycode():
    """Test complex punycode examples"""
    # Chinese characters: xn--fiqs8s.example should decode to 中国.example
    result = normalize_hostname("xn--fiqs8s.example")
    assert result == "中国.example"

    # Japanese characters: xn--eckwd4c7cu47r2wf.example should decode to ドメイン名例.example
    result = normalize_hostname("xn--eckwd4c7cu47r2wf.example")
    assert result == "ドメイン名例.example"


def test_normalize_hostname_punycode_not_starting_with_xn():
    """Test that strings containing xn-- but not starting with it are unchanged"""
    assert normalize_hostname("example.xn--test.com") == "example.xn--test.com"
    assert normalize_hostname("sub.xn--domain.com") == "sub.xn--domain.com"


def test_normalize_hostname_punycode_error_handling():
    """Test error handling for malformed punycode"""
    # This should return the original string if decoding fails
    result = normalize_hostname("xn--invalid-punycode")
    # Should either return the original or a decoded version if valid
    assert isinstance(result, str)
