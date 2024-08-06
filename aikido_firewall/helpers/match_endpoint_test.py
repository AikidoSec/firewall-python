from .build_route_from_url import build_route_from_url
from .match_endpoint import match_endpoint

url = "http://localhost:4000/posts/3"


class SampleContext:
    remote_address = "::1"
    method = "POST"
    url = url
    query = {}
    headers = {}
    body = None
    cookies = {}
    route_params = {}
    source = "express"
    route = build_route_from_url(url)


def test_invalid_url_and_no_route():
    context = SampleContext()
    context.route = None
    context.url = "abc"
    assert match_endpoint(context, []) is None


def test_no_url_and_no_route():
    context = SampleContext()
    context.route = None
    context.url = None
    assert match_endpoint(context, []) is None


def test_no_method():
    context = SampleContext()
    context.method = None
    assert match_endpoint(context, []) is None


def test_returns_undefined_if_nothing_found():
    context = SampleContext()
    assert match_endpoint(context, []) is None


def test_returns_endpoint_based_on_route():
    context = SampleContext()
    assert match_endpoint(
        context,
        [
            {
                "method": "POST",
                "route": "/posts/:number",
                "rate_limiting": {
                    "enabled": True,
                    "max_requests": 10,
                    "window_size_in_ms": 1000,
                },
                "force_protection_off": False,
            },
        ],
    ) == {
        "endpoint": {
            "method": "POST",
            "route": "/posts/:number",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        "route": "/posts/:number",
    }


def test_returns_endpoint_based_on_relative_url():
    context = SampleContext()
    context.route = build_route_from_url("/posts/3")
    context.url = "/posts/3"
    assert match_endpoint(
        context,
        [
            {
                "method": "POST",
                "route": "/posts/:number",
                "rate_limiting": {
                    "enabled": True,
                    "max_requests": 10,
                    "window_size_in_ms": 1000,
                },
                "force_protection_off": False,
            },
        ],
    ) == {
        "endpoint": {
            "method": "POST",
            "route": "/posts/:number",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        "route": "/posts/:number",
    }


def test_returns_endpoint_based_on_wildcard():
    context = SampleContext()
    context.route = None
    assert match_endpoint(
        context,
        [
            {
                "method": "*",
                "route": "/posts/*",
                "rate_limiting": {
                    "enabled": True,
                    "max_requests": 10,
                    "window_size_in_ms": 1000,
                },
                "force_protection_off": False,
            },
        ],
    ) == {
        "endpoint": {
            "method": "*",
            "route": "/posts/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        "route": "/posts/*",
    }


def test_returns_endpoint_based_on_wildcard_with_relative_url():
    context = SampleContext()
    context.route = None
    context.url = "/posts/3"
    assert match_endpoint(
        context,
        [
            {
                "method": "*",
                "route": "/posts/*",
                "rate_limiting": {
                    "enabled": True,
                    "max_requests": 10,
                    "window_size_in_ms": 1000,
                },
                "force_protection_off": False,
            },
        ],
    ) == {
        "endpoint": {
            "method": "*",
            "route": "/posts/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        "route": "/posts/*",
    }


def test_favors_more_specific_wildcard():
    context = SampleContext()
    context.route = None
    context.url = "http://localhost:4000/posts/3/comments/10"
    assert match_endpoint(
        context,
        [
            {
                "method": "*",
                "route": "/posts/*",
                "rate_limiting": {
                    "enabled": True,
                    "max_requests": 10,
                    "window_size_in_ms": 1000,
                },
                "force_protection_off": False,
            },
            {
                "method": "*",
                "route": "/posts/*/comments/*",
                "rate_limiting": {
                    "enabled": True,
                    "max_requests": 10,
                    "window_size_in_ms": 1000,
                },
                "force_protection_off": False,
            },
        ],
    ) == {
        "endpoint": {
            "method": "*",
            "route": "/posts/*/comments/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        "route": "/posts/*/comments/*",
    }


def test_matches_wildcard_route_with_specific_method():
    context = SampleContext()
    context.route = None
    context.url = "http://localhost:4000/posts/3/comments/10"
    context.method = "POST"
    assert match_endpoint(
        context,
        [
            {
                "method": "POST",
                "route": "/posts/*/comments/*",
                "rate_limiting": {
                    "enabled": True,
                    "max_requests": 10,
                    "window_size_in_ms": 1000,
                },
                "force_protection_off": False,
            },
        ],
    ) == {
        "endpoint": {
            "method": "POST",
            "route": "/posts/*/comments/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        "route": "/posts/*/comments/*",
    }


def test_prefers_specific_route_over_wildcard():
    context = SampleContext()
    context.route = "/api/coach"
    context.url = "http://localhost:4000/api/coach"
    context.method = "POST"
    assert match_endpoint(
        context,
        [
            {
                "method": "*",
                "route": "/api/*",
                "force_protection_off": False,
                "rate_limiting": {
                    "enabled": True,
                    "max_requests": 20,
                    "window_size_in_ms": 60000,
                },
            },
            {
                "method": "POST",
                "route": "/api/coach",
                "force_protection_off": False,
                "rate_limiting": {
                    "enabled": True,
                    "max_requests": 100,
                    "window_size_in_ms": 60000,
                },
            },
        ],
    ) == {
        "endpoint": {
            "method": "POST",
            "route": "/api/coach",
            "force_protection_off": False,
            "rate_limiting": {
                "enabled": True,
                "max_requests": 100,
                "window_size_in_ms": 60000,
            },
        },
        "route": "/api/coach",
    }
