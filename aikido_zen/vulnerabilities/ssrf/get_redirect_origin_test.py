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


def test_avoids_infinite_loops_with_unrelated_cyclic_redirects():
    result = get_redirect_origin(
        [
            # Unrelated cyclic redirects
            {
                "source": create_url("https://cycle.com/a"),
                "destination": create_url("https://cycle.com/b"),
            },
            {
                "source": create_url("https://cycle.com/b"),
                "destination": create_url("https://cycle.com/c"),
            },
            {
                "source": create_url("https://cycle.com/c"),
                "destination": create_url("https://cycle.com/a"),
            },
            # Relevant redirects
            {
                "source": create_url("https://start.com"),
                "destination": create_url("https://middle.com"),
            },
            {
                "source": create_url("https://middle.com"),
                "destination": create_url("https://end.com"),
            },
        ],
        "end.com",
        443,
    )
    assert result == create_url("https://start.com")


def test_handles_multiple_requests_with_overlapping_redirects():
    result = get_redirect_origin(
        [
            # Overlapping redirects
            {
                "source": create_url("https://site1.com"),
                "destination": create_url("https://site2.com"),
            },
            {
                "source": create_url("https://site2.com"),
                "destination": create_url("https://site3.com"),
            },
            {
                "source": create_url("https://site3.com"),
                "destination": create_url("https://site1.com"),  # Cycle
            },
            # Relevant redirects
            {
                "source": create_url("https://origin.com"),
                "destination": create_url("https://destination.com"),
            },
        ],
        "destination.com",
        443,
    )
    assert result == create_url("https://origin.com")


def test_avoids_infinite_loops_when_cycles_are_part_of_the_redirect_chain():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://start.com"),
                "destination": create_url("https://loop.com/a"),
            },
            {
                "source": create_url("https://loop.com/a"),
                "destination": create_url("https://loop.com/b"),
            },
            {
                "source": create_url("https://loop.com/b"),
                "destination": create_url("https://loop.com/c"),
            },
            {
                "source": create_url("https://loop.com/c"),
                "destination": create_url("https://loop.com/a"),  # Cycle here
            },
        ],
        "loop.com",
        443,
    )
    assert result == create_url("https://start.com")


def test_redirects_with_query_parameters():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://example.com"),
                "destination": create_url("https://example.com?param=value"),
            },
        ],
        "example.com",
        443,
    )
    assert result == create_url("https://example.com")


def test_redirects_with_fragment_identifiers():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://example.com"),
                "destination": create_url("https://example.com#section"),
            },
        ],
        "example.com",
        443,
    )
    assert result == create_url("https://example.com")


def test_redirects_with_different_protocols():
    result = get_redirect_origin(
        [
            {
                "source": create_url("http://example.com"),
                "destination": create_url("https://example.com"),
            },
        ],
        "example.com",
        443,
    )
    assert result == create_url("http://example.com")


def test_redirects_with_different_ports():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://example.com"),
                "destination": create_url("https://example.com:8080"),
            },
        ],
        "example.com",
        8080,
    )
    assert result == create_url("https://example.com")


def test_redirects_with_paths():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://example.com"),
                "destination": create_url("https://example.com/home"),
            },
            {
                "source": create_url("https://example.com/home"),
                "destination": create_url("https://example.com/home/welcome"),
            },
        ],
        "example.com",
        443,
    )
    assert result == create_url("https://example.com")


def test_multiple_redirects_to_same_destination():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://a.com"),
                "destination": create_url("https://d.com"),
            },
            {
                "source": create_url("https://b.com"),
                "destination": create_url("https://d.com"),
            },
            {
                "source": create_url("https://c.com"),
                "destination": create_url("https://d.com"),
            },
        ],
        "d.com",
        443,
    )
    assert result == create_url("https://a.com")


def test_multiple_redirect_paths_to_same_url():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://x.com"),
                "destination": create_url("https://y.com"),
            },
            {
                "source": create_url("https://y.com"),
                "destination": create_url("https://z.com"),
            },
            {
                "source": create_url("https://a.com"),
                "destination": create_url("https://b.com"),
            },
            {
                "source": create_url("https://b.com"),
                "destination": create_url("https://z.com"),
            },
        ],
        "z.com",
        443,
    )
    assert result == create_url("https://x.com")


def test_returns_undefined_when_source_and_destination_are_same_url():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://example.com"),
                "destination": create_url("https://example.com"),
            },
        ],
        "example.com",
        443,
    )
    assert result is None


def test_handles_very_long_redirect_chains():
    redirects = []
    for i in range(100):
        redirects.append(
            {
                "source": create_url(f"https://example.com/{i}"),
                "destination": create_url(f"https://example.com/{i + 1}"),
            }
        )

    result = get_redirect_origin(redirects, "example.com", 443)
    assert result == create_url("https://example.com/0")


def test_handles_redirects_with_cycles_longer_than_one_redirect():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://a.com"),
                "destination": create_url("https://b.com"),
            },
            {
                "source": create_url("https://b.com"),
                "destination": create_url("https://c.com"),
            },
            {
                "source": create_url("https://c.com"),
                "destination": create_url("https://a.com"),
            },
        ],
        "a.com",
        443,
    )
    assert result is None


def test_handles_redirects_with_different_query_parameters():
    result = get_redirect_origin(
        [
            {
                "source": create_url("https://example.com"),
                "destination": create_url("https://example.com?param=1"),
            },
            {
                "source": create_url("https://example.com?param=1"),
                "destination": create_url("https://example.com?param=2"),
            },
        ],
        "example.com",
        443,
    )
    assert result == create_url("https://example.com")
