import pytest
from unittest.mock import MagicMock
from .ip_allowed_to_access_route import ip_allowed_to_access_route


def gen_route_metadata(
    url="http://localhost:4000/posts/3", method="GET", route="/posts/:id"
):
    return {"url": url, "route": route, "method": method}


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
    context = gen_route_metadata()
    reporter = create_reporter(["1.2.3.4"])
    assert ip_allowed_to_access_route("::1", context, reporter) is True


def test_always_allows_request_if_no_match():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = gen_route_metadata(route="/", method="GET")
    assert ip_allowed_to_access_route("1.2.3.4", modified_context, reporter) is True


def test_always_allows_request_if_allowed_ip_address():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert ip_allowed_to_access_route("1.2.3.4", modified_context, reporter) is True


def test_always_allows_request_if_localhost():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert ip_allowed_to_access_route("::1", modified_context, reporter) is True


def test_blocks_request_if_no_ip_address():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert ip_allowed_to_access_route(None, modified_context, reporter) is False


def test_allows_request_if_configuration_is_broken():
    reporter = create_reporter({})  # Broken configuration
    modified_context = gen_route_metadata(method="POST", route="/posts/:id")
    assert ip_allowed_to_access_route("3.4.5.6", modified_context, reporter) is True


def test_allows_request_if_allowed_ip_addresses_is_empty():
    reporter = create_reporter([])
    context = gen_route_metadata()
    assert ip_allowed_to_access_route("3.4.5.6", context, reporter) is True


def test_blocks_request_if_not_allowed_ip_address():
    reporter = create_reporter(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert ip_allowed_to_access_route("3.4.5.6", modified_context, reporter) is False


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
    modified_context = gen_route_metadata(method="POST", route="/posts/:id")
    assert ip_allowed_to_access_route("3.4.5.6", modified_context, reporter) is False


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
    modified_context_allowed = gen_route_metadata()
    assert (
        ip_allowed_to_access_route("1.2.3.4", modified_context_allowed, reporter)
        is True
    )

    modified_context_blocked = gen_route_metadata()
    assert (
        ip_allowed_to_access_route("3.4.5.6", modified_context_blocked, reporter)
        is False
    )
