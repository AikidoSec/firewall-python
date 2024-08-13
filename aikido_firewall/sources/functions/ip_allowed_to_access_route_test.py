import pytest
from unittest.mock import MagicMock
from .ip_allowed_to_access_route import ip_allowed_to_access_route


class SampleContext:
    def __init__(
        self,
        remote_address="::1",
        method="POST",
        url="http://localhost:4000/posts/3",
        query=None,
        headers=None,
        body=None,
        cookies=None,
        route_params=None,
        source="express",
        route="/posts/:id",
    ):
        self.remote_address = remote_address
        self.method = method
        self.url = url
        self.query = query if query is not None else {}
        self.headers = headers if headers is not None else {}
        self.body = body
        self.cookies = cookies if cookies is not None else {}
        self.route_params = route_params if route_params is not None else {}
        self.source = source
        self.route = route


def create_reporter(allowed_ip_addresses):
    # Mock the reporter with the necessary attributes
    reporter = MagicMock()
    reporter.conf.get_endpoints = lambda x: [
        {
            "route": "/posts/:id",
            "method": "POST",
            "allowedIPAddresses": allowed_ip_addresses,
            "force_protection_off": False,
        },
    ]
    return reporter


def test_always_allows_request_if_not_production():
    context = SampleContext()
    reporter = create_reporter(["1.2.3.4"])
    assert ip_allowed_to_access_route(context, reporter) is True


def test_always_allows_request_if_no_match():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = SampleContext(route="/", method="GET", remote_address="1.2.3.4")
    assert ip_allowed_to_access_route(modified_context, reporter) is True


def test_always_allows_request_if_allowed_ip_address():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = SampleContext(remote_address="1.2.3.4")
    assert ip_allowed_to_access_route(modified_context, reporter) is True


def test_always_allows_request_if_localhost():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = SampleContext(remote_address="::1")
    assert ip_allowed_to_access_route(modified_context, reporter) is True


def test_blocks_request_if_no_ip_address():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = SampleContext(remote_address=None)
    assert ip_allowed_to_access_route(modified_context, reporter) is False


def test_allows_request_if_configuration_is_broken():
    reporter = create_reporter({})  # Broken configuration
    modified_context = SampleContext(
        remote_address="3.4.5.6", method="POST", route="/posts/:id"
    )
    assert ip_allowed_to_access_route(modified_context, reporter) is True


def test_allows_request_if_allowed_ip_addresses_is_empty():
    reporter = create_reporter([])
    context = SampleContext(remote_address="3.4.5.6")
    assert ip_allowed_to_access_route(context, reporter) is True


def test_blocks_request_if_not_allowed_ip_address():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = SampleContext(remote_address="3.4.5.6")
    assert ip_allowed_to_access_route(modified_context, reporter) is False


def test_checks_every_matching_endpoint():
    reporter = MagicMock()
    reporter.conf.get_endpoints = lambda x: [
        {
            "route": "/posts/:id",
            "method": "POST",
            "allowedIPAddresses": ["3.4.5.6"],
            "force_protection_off": False,
        },
        {
            "route": "/posts/*",
            "method": "POST",
            "allowedIPAddresses": ["1.2.3.4"],
            "force_protection_off": False,
        },
    ]
    modified_context = SampleContext(
        remote_address="3.4.5.6", method="POST", route="/posts/:id"
    )
    assert ip_allowed_to_access_route(modified_context, reporter) is False


def test_if_allowed_ips_is_empty_or_broken():
    reporter = MagicMock()
    reporter.conf.get_endpoints = lambda x: [
        {
            "route": "/posts/:id",
            "method": "POST",
            "allowedIPAddresses": [],
            "force_protection_off": False,
        },
        {
            "route": "/posts/*",
            "method": "POST",
            "allowedIPAddresses": {},  # Broken configuration
            "force_protection_off": False,
        },
        {
            "route": "/posts/*",
            "method": "POST",
            "allowedIPAddresses": ["1.2.3.4"],
            "force_protection_off": False,
        },
    ]
    modified_context_allowed = SampleContext(remote_address="1.2.3.4")
    assert ip_allowed_to_access_route(modified_context_allowed, reporter) is True

    modified_context_blocked = SampleContext(remote_address="3.4.5.6")
    assert ip_allowed_to_access_route(modified_context_blocked, reporter) is False
