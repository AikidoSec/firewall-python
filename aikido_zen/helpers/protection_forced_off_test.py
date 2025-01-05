import pytest
from .protection_forced_off import protection_forced_off


def sample_route_metadata(route=None, url=None):
    # This is a mock function to simulate the behavior of the actual sample_route_metadata function.
    return {"route": route, "url": url, "method": "POST"}


def test_protection_forced_off_with_protection_off():
    route_metadata = sample_route_metadata(
        url="http://example.com/posts/3", route="/posts/:number"
    )
    endpoints = [
        {
            "method": "POST",
            "route": "/posts/:number",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": True,  # This should return True
        },
    ]
    assert protection_forced_off(route_metadata, endpoints) is True


def test_protection_forced_off_with_protection_on():
    route_metadata = sample_route_metadata(
        url="http://example.com/posts/3", route="/posts/:number"
    )
    endpoints = [
        {
            "method": "POST",
            "route": "/posts/:number",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": False,  # This should return False
        },
    ]
    assert protection_forced_off(route_metadata, endpoints) is False


def test_protection_forced_off_with_no_matches():
    route_metadata = sample_route_metadata(
        url="http://example.com/unknown", route="/unknown"
    )
    endpoints = [
        {
            "method": "GET",
            "route": "/posts/:number",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": False,
        },
    ]
    assert protection_forced_off(route_metadata, endpoints) is False


def test_protection_forced_off_with_empty_endpoints():
    route_metadata = sample_route_metadata(
        url="http://example.com/posts/3", route="/posts/:number"
    )
    endpoints = []
    assert protection_forced_off(route_metadata, endpoints) is False


def test_protection_forced_off_with_multiple_endpoints():
    route_metadata = sample_route_metadata(
        url="http://example.com/posts/3", route="/posts/:number"
    )
    endpoints = [
        {
            "method": "POST",
            "route": "/posts/:number",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": True,  # This should be the one returned
        },
        {
            "method": "POST",
            "route": "/posts/:number",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": False,
        },
    ]
    assert protection_forced_off(route_metadata, endpoints) is True


def test_protection_forced_off_with_multiple_endpoints2():
    route_metadata = sample_route_metadata(
        url="http://example.com/posts/3", route="/posts/:number"
    )
    endpoints = [
        {
            "method": "POST",
            "route": "/posts/:number",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": False,  # This should be the one returned
        },
        {
            "method": "POST",
            "route": "/posts/:number",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": True,
        },
    ]
    assert protection_forced_off(route_metadata, endpoints) is False
