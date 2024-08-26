import pytest
from unittest.mock import MagicMock
from .ip_allowed_to_access_route import ip_allowed_to_access_route


def gen_route_metadata(
    url="http://localhost:4000/posts/3", method="GET", route="/posts/:id"
):
    return {"url": url, "route": route, "method": method}


def create_connection_manager(allowed_ip_addresses):
    # Mock the connection_manager with the necessary attributes
    connection_manager = MagicMock()
    connection_manager.conf.get_endpoints = lambda x: [
        {
            "route": "/posts/:id",
            "method": "POST",
            "allowedIPAddresses": allowed_ip_addresses,
            "force_protection_off": False,
        },
    ]
    return connection_manager


def test_always_allows_request_if_not_production():
    context = gen_route_metadata()
    connection_manager = create_connection_manager(["1.2.3.4"])
    assert ip_allowed_to_access_route("::1", context, connection_manager) is True


def test_always_allows_request_if_no_match():
    connection_manager = create_connection_manager(["1.2.3.4"])
    modified_context = gen_route_metadata(route="/", method="GET")
    assert (
        ip_allowed_to_access_route("1.2.3.4", modified_context, connection_manager)
        is True
    )


def test_always_allows_request_if_allowed_ip_address():
    connection_manager = create_connection_manager(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert (
        ip_allowed_to_access_route("1.2.3.4", modified_context, connection_manager)
        is True
    )


def test_always_allows_request_if_localhost():
    connection_manager = create_connection_manager(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert (
        ip_allowed_to_access_route("::1", modified_context, connection_manager) is True
    )


def test_blocks_request_if_no_ip_address():
    connection_manager = create_connection_manager(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert (
        ip_allowed_to_access_route(None, modified_context, connection_manager) is False
    )


def test_allows_request_if_configuration_is_broken():
    connection_manager = create_connection_manager({})  # Broken configuration
    modified_context = gen_route_metadata(method="POST", route="/posts/:id")
    assert (
        ip_allowed_to_access_route("3.4.5.6", modified_context, connection_manager)
        is True
    )


def test_allows_request_if_allowed_ip_addresses_is_empty():
    connection_manager = create_connection_manager([])
    context = gen_route_metadata()
    assert ip_allowed_to_access_route("3.4.5.6", context, connection_manager) is True


def test_blocks_request_if_not_allowed_ip_address():
    connection_manager = create_connection_manager(["1.2.3.4"])
    modified_context = gen_route_metadata()
    assert (
        ip_allowed_to_access_route("3.4.5.6", modified_context, connection_manager)
        is False
    )


def test_checks_every_matching_endpoint():
    connection_manager = MagicMock()
    connection_manager.conf.get_endpoints = lambda x: [
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
    assert (
        ip_allowed_to_access_route("3.4.5.6", modified_context, connection_manager)
        is False
    )


def test_if_allowed_ips_is_empty_or_broken():
    connection_manager = MagicMock()
    connection_manager.conf.get_endpoints = lambda x: [
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
        ip_allowed_to_access_route(
            "1.2.3.4", modified_context_allowed, connection_manager
        )
        is True
    )

    modified_context_blocked = gen_route_metadata()
    assert (
        ip_allowed_to_access_route(
            "3.4.5.6", modified_context_blocked, connection_manager
        )
        is False
    )
