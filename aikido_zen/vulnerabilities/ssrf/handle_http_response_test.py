import socket
from urllib.parse import urlparse

import pytest

from aikido_zen.context import current_context, get_current_context
from aikido_zen.test_utils import generate_and_set_context
from aikido_zen.thread.thread_cache import get_cache
from .handle_http_response import handle_http_response
from .inspect_getaddrinfo_result import inspect_getaddrinfo_result


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    get_cache().reset()
    current_context.set(None)


class Response:
    def __init__(self, location):
        self.code = 302
        self.headers = {"Location": location}


def redirect(source, location):
    handle_http_response(Response(location), urlparse(source))


def recorded_redirects():
    return [
        (r["source"].hostname, r["destination"].hostname)
        for r in get_current_context().outgoing_req_redirects
    ]


def test_records_redirect_from_user_input():
    generate_and_set_context(value="http://a.example.com/start")
    redirect("http://a.example.com:80/start", "http://b.example.net/next")
    assert recorded_redirects() == [("a.example.com", "b.example.net")]


def test_records_every_hop_of_a_chain_across_hosts():
    generate_and_set_context(value="http://a.example.com/start")
    redirect("http://a.example.com:80/start", "http://b.example.net/next")
    redirect("http://b.example.net:80/next", "http://c.example.org/admin")
    assert recorded_redirects() == [
        ("a.example.com", "b.example.net"),
        ("b.example.net", "c.example.org"),
    ]


def test_ignores_redirect_not_started_by_user_input():
    generate_and_set_context(value="http://a.example.com/start")
    redirect("http://x.example.com:80/", "http://y.example.com/")
    assert recorded_redirects() == []


def test_reports_private_ip_at_the_end_of_a_chain_across_hosts():
    generate_and_set_context(value="http://a.example.com/start")
    redirect("http://a.example.com:80/start", "http://b.example.net/next")
    redirect("http://b.example.net:80/next", "http://c.example.org/admin")

    result = inspect_getaddrinfo_result(
        dns_results=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 80))],
        hostname="c.example.org",
        port=80,
    )

    assert result["kind"] == "ssrf"
    assert result["source"] == "body"
    assert result["payload"] == "http://a.example.com/start"


@pytest.mark.parametrize(
    "location, destination",
    [
        ("//b.example.net/next", "http://b.example.net/next"),
        ("/next", "http://a.example.com:80/next"),
    ],
)
def test_resolves_a_relative_location_against_the_request_url(location, destination):
    generate_and_set_context(value="http://a.example.com/start")
    redirect("http://a.example.com:80/start", location)
    (recorded,) = get_current_context().outgoing_req_redirects
    assert recorded["destination"].geturl() == destination


@pytest.mark.parametrize(
    "user_input, source, port",
    [
        ("http://a.example.com/start", "http://a.example.com:80/start", 80),
        ("https://a.example.com/start", "http://a.example.com:443/start", 443),
    ],
)
def test_reports_private_ip_after_a_protocol_relative_redirect(
    user_input, source, port
):
    generate_and_set_context(value=user_input)
    redirect(source, "//c.example.org/admin")

    result = inspect_getaddrinfo_result(
        dns_results=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", port))],
        hostname="c.example.org",
        port=port,
    )

    assert result["kind"] == "ssrf"
    assert result["payload"] == user_input
