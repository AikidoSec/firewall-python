import pytest
from urllib.parse import urlparse, urlunparse
from .get_redirect_origin import get_redirect_origin


# Helper function to create URL objects
def create_url(href):
    return urlparse(href)


# Test cases
def test_get_redirect_origin():
    assert get_redirect_origin(
        [
            {
                "source": create_url("https://example.com"),
                "destination": create_url("https://hackers.com"),
            },
        ],
        "hackers.com",
        443,
    ) == create_url("https://example.com")

    assert get_redirect_origin(
        [
            {
                "source": create_url("https://example.com"),
                "destination": create_url("https://example.com/2"),
            },
            {
                "source": create_url("https://example.com/2"),
                "destination": create_url("https://hackers.com/test"),
            },
        ],
        "hackers.com",
        443,
    ) == create_url("https://example.com")


def test_get_redirect_origin_no_redirects():
    assert (
        get_redirect_origin(
            [],
            "hackers.com",
            443,
        )
        is None
    )
    assert (
        get_redirect_origin(
            None,
            "hackers.com",
            443,
        )
        is None
    )


def test_get_redirect_origin_not_a_destination():
    assert (
        get_redirect_origin(
            [
                {
                    "source": create_url("https://example.com"),
                    "destination": create_url("https://hackers.com"),
                },
            ],
            "example.com",
            443,
        )
        is None
    )


def test_get_redirect_origin_not_in_redirects():
    assert (
        get_redirect_origin(
            [
                {
                    "source": create_url("https://example.com"),
                    "destination": create_url("https://hackers.com"),
                },
            ],
            "example.com",
            443,
        )
        is None
    )


def test_get_redirect_origin_multiple_redirects():
    assert get_redirect_origin(
        [
            {
                "source": create_url("https://example.com"),
                "destination": create_url("https://example.com/2"),
            },
            {
                "source": create_url("https://example.com/2"),
                "destination": create_url("https://hackers.com/test"),
            },
            {
                "source": create_url("https://hackers.com/test"),
                "destination": create_url("https://another.com"),
            },
        ],
        "hackers.com",
        443,
    ) == create_url("https://example.com")


# To run the tests, use the command: pytest <filename>.py
