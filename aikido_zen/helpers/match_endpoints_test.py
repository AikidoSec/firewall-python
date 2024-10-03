import pytest
from .build_route_from_url import build_route_from_url
from .match_endpoints import match_endpoints


def sample_route_metadata(
    route="/posts/:number", method="POST", url="http://localhost:4000/posts/3"
):
    return {"method": method, "url": url, "route": route}


def test_invalid_url_and_no_route():
    assert match_endpoints(sample_route_metadata(route=None, url="abc"), []) == None


def test_no_url_and_no_route():
    assert match_endpoints(sample_route_metadata(route=None, url=None), []) == None


def test_no_method():
    assert match_endpoints(sample_route_metadata(method=None), []) == None


def test_it_returns_undefined_if_nothing_found():
    assert match_endpoints(sample_route_metadata(), []) == None


def test_it_returns_endpoint_based_on_route():
    endpoints = [
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
    assert match_endpoints(sample_route_metadata(), endpoints) == endpoints


def test_it_returns_endpoint_based_on_relative_url():
    assert match_endpoints(
        sample_route_metadata(url="/posts/3"),
        [
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
        ],
    ) == [
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


def test_it_returns_endpoint_based_on_wildcard():
    assert match_endpoints(
        sample_route_metadata(route=None),
        [
            {
                "method": "*",
                "route": "/posts/*",
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 10,
                    "windowSizeInMS": 1000,
                },
                "forceProtectionOff": False,
            },
        ],
    ) == [
        {
            "method": "*",
            "route": "/posts/*",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": False,
        },
    ]


def test_it_returns_endpoint_based_on_wildcard_with_relative_url():
    assert match_endpoints(
        sample_route_metadata(route=None, url="/posts/3"),
        [
            {
                "method": "*",
                "route": "/posts/*",
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 10,
                    "windowSizeInMS": 1000,
                },
                "forceProtectionOff": False,
            },
        ],
    ) == [
        {
            "method": "*",
            "route": "/posts/*",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": False,
        },
    ]


def test_it_favors_more_specific_wildcard():
    assert match_endpoints(
        sample_route_metadata(
            url="http://localhost:4000/posts/3/comments/10", route=None
        ),
        [
            {
                "method": "*",
                "route": "/posts/*",
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 10,
                    "windowSizeInMS": 1000,
                },
                "forceProtectionOff": False,
            },
            {
                "method": "*",
                "route": "/posts/*/comments/*",
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 10,
                    "windowSizeInMS": 1000,
                },
                "forceProtectionOff": False,
            },
        ],
    ) == [
        {
            "method": "*",
            "route": "/posts/*/comments/*",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": False,
        },
        {
            "method": "*",
            "route": "/posts/*",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": False,
        },
    ]


def test_it_matches_wildcard_route_with_specific_method():
    assert match_endpoints(
        sample_route_metadata(
            url="http://localhost:4000/posts/3/comments/10", route=None
        ),
        [
            {
                "method": "POST",
                "route": "/posts/*/comments/*",
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 10,
                    "windowSizeInMS": 1000,
                },
                "forceProtectionOff": False,
            },
        ],
    ) == [
        {
            "method": "POST",
            "route": "/posts/*/comments/*",
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 10,
                "windowSizeInMS": 1000,
            },
            "forceProtectionOff": False,
        },
    ]


def test_it_prefers_specific_route_over_wildcard():
    assert match_endpoints(
        sample_route_metadata(
            url="http://localhost:4000/api/coach", route="/api/coach"
        ),
        [
            {
                "method": "*",
                "route": "/api/*",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 20,
                    "windowSizeInMS": 60000,
                },
            },
            {
                "method": "POST",
                "route": "/api/coach",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 100,
                    "windowSizeInMS": 60000,
                },
            },
        ],
    ) == [
        {
            "method": "POST",
            "route": "/api/coach",
            "forceProtectionOff": False,
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 100,
                "windowSizeInMS": 60000,
            },
        },
        {
            "method": "*",
            "route": "/api/*",
            "forceProtectionOff": False,
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 20,
                "windowSizeInMS": 60000,
            },
        },
    ]
