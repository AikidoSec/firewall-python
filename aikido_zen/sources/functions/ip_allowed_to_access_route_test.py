import pytest
from unittest.mock import MagicMock
from .ip_allowed_to_access_route import ip_allowed_to_access_route
from aikido_zen.helpers.iplist import IPList


def gen_route_metadata(
    url="http://localhost:4000/posts/3", method="GET", route="/posts/:id"
):
    return {"url": url, "route": route, "method": method}


def gen_endpoints(allowed_ip_addresses):
    return [
        {
            "route": "/posts/:id",
            "method": "POST",
            "allowedIPAddresses": (
                IPList(allowed_ip_addresses) if len(allowed_ip_addresses) > 0 else None
            ),
            "force_protection_off": False,
        },
    ]


def test_always_allows_request_if_not_production():
    context = gen_route_metadata()
    endpoints = gen_endpoints(["1.2.3.4"])
    assert ip_allowed_to_access_route("::1", context, endpoints) is True


def test_always_allows_request_if_no_match():
    endpoints = gen_endpoints(["1.2.3.4"])
    modified_context = gen_route_metadata(route="/", method="GET")
    assert ip_allowed_to_access_route("1.2.3.4", modified_context, endpoints) is True


def test_always_allows_request_if_allowed_ip_address():
    endpoints = gen_endpoints(["1.2.3.4", "10.0.0.0/24"])
    modified_context = gen_route_metadata()
    assert ip_allowed_to_access_route("1.2.3.4", modified_context, endpoints) is True
    assert ip_allowed_to_access_route("10.0.0.2", modified_context, endpoints) is True


def test_always_allows_request_if_localhost():
    endpoints = gen_endpoints(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert ip_allowed_to_access_route("::1", modified_context, endpoints) is True


def test_blocks_request_if_no_ip_address():
    endpoints = gen_endpoints(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert ip_allowed_to_access_route(None, modified_context, endpoints) is False


def test_allows_request_if_configuration_is_broken():
    endpoints = gen_endpoints({})  # Broken configuration
    modified_context = gen_route_metadata(method="POST", route="/posts/:id")
    assert ip_allowed_to_access_route("3.4.5.6", modified_context, endpoints) is True


def test_allows_request_if_allowed_ip_addresses_is_empty():
    endpoints = gen_endpoints([])
    context = gen_route_metadata()
    assert ip_allowed_to_access_route("3.4.5.6", context, endpoints) is True


def test_blocks_request_if_not_allowed_ip_address():
    endpoints = gen_endpoints(["1.2.3.4", "10.0.0.0/24"])
    modified_context = gen_route_metadata()
    assert ip_allowed_to_access_route("3.4.5.6", modified_context, endpoints) is False
    assert ip_allowed_to_access_route("10.1.1.1", modified_context, endpoints) is False


def test_checks_every_matching_endpoint():
    endpoints = [
        {
            "route": "/posts/:id",
            "method": "POST",
            "allowedIPAddresses": IPList(["3.4.5.6"]),
            "force_protection_off": False,
        },
        {
            "route": "/posts/*",
            "method": "POST",
            "allowedIPAddresses": IPList(["1.2.3.4"]),
            "force_protection_off": False,
        },
    ]
    modified_context = gen_route_metadata(method="POST", route="/posts/:id")
    assert ip_allowed_to_access_route("3.4.5.6", modified_context, endpoints) is False


def test_if_allowed_ips_is_empty_or_broken():
    endpoints = [
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
            "allowedIPAddresses": IPList(["1.2.3.4"]),
            "force_protection_off": False,
        },
    ]
    modified_context_allowed = gen_route_metadata()
    assert (
        ip_allowed_to_access_route("1.2.3.4", modified_context_allowed, endpoints)
        is True
    )

    modified_context_blocked = gen_route_metadata()
    assert (
        ip_allowed_to_access_route("3.4.5.6", modified_context_blocked, endpoints)
        is False
    )
