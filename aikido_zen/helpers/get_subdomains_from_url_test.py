import pytest
from aikido_zen.helpers.get_subdomains_from_url import get_subdomains_from_url


def test_get_subdomains_from_url():
    # Test cases with expected results
    test_cases = [
        # Test with a standard URL
        ("http://tobi.ferrets.example.com", ["tobi", "ferrets"]),
        # Test with a URL that has no subdomains
        ("http://example.com", []),
        # Test with a URL that has multiple subdomains
        ("http://a.b.c.example.com", ["a", "b", "c"]),
        # Test with a URL that has a port
        ("http://tobi.ferrets.example.com:8080", ["tobi", "ferrets"]),
        # Test with a URL that has only the main domain
        ("http://localhost", []),
        # Test with an invalid URL
        ("http://.com", []),
        # Test with an empty string
        ("", []),
        # Test with a URL with subdomains and a path
        ("http://tobi.ferrets.example.com/path/to/resource", ["tobi", "ferrets"]),
        ({}, []),
        (None, []),
    ]

    for url, expected in test_cases:
        assert get_subdomains_from_url(url) == expected
