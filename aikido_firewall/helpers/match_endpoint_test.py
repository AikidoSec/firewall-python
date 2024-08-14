from .build_route_from_url import build_route_from_url
from .match_endpoint import match_endpoint

url = "http://localhost:4000/posts/3"


def sample_route_metadata():
    return {"method": "POST", "url": url, "route": build_route_from_url(url)}


def test_invalid_url_and_no_route():
    context = sample_route_metadata()
    context["route"] = None
    context["url"] = "abc"
    assert match_endpoint(context, []) is None


def test_no_url_and_no_route():
    context = sample_route_metadata()
    context["route"] = None
    context["url"] = None
    assert match_endpoint(context, []) is None


def test_no_method():
    context = sample_route_metadata()
    context["method"] = None
    assert match_endpoint(context, []) is None


def test_returns_undefined_if_nothing_found():
    context = sample_route_metadata()
    assert match_endpoint(context, []) is None


def test_returns_endpoint_based_on_route():
    context = sample_route_metadata()
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
    context = sample_route_metadata()
    context["route"] = build_route_from_url("/posts/3")
    context["url"] = "/posts/3"
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
    context = sample_route_metadata()
    context["route"] = None
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
    context = sample_route_metadata()
    context["route"] = None
    context["url"] = "/posts/3"
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
    context = sample_route_metadata()
    context["route"] = None
    context["url"] = "http://localhost:4000/posts/3/comments/10"
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
    context = sample_route_metadata()
    context["route"] = None
    context["url"] = "http://localhost:4000/posts/3/comments/10"
    context["method"] = "POST"
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
    context = sample_route_metadata()
    context["route"] = "/api/coach"
    context["url"] = "http://localhost:4000/api/coach"
    context["method"] = "POST"
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


def test_returns_multiple_endpoints_with_wildcards():
    context = sample_route_metadata()
    context["route"] = None
    context["url"] = "http://localhost:4000/posts/3/comments/10"
    context["method"] = "GET"

    endpoints = [
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
                "max_requests": 5,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        {
            "method": "GET",
            "route": "/posts/*/comments/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 3,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
    ]

    result = match_endpoint(context, endpoints, multi=True)

    assert len(result) == 3  # Expecting two matches
    assert all(
        endpoint["endpoint"]["route"].startswith("/posts/") for endpoint in result
    )
    assert any(
        endpoint["endpoint"]["route"] == "/posts/*/comments/*" for endpoint in result
    )
    assert any(endpoint["endpoint"]["route"] == "/posts/*" for endpoint in result)


def test_returns_multiple_endpoints_with_specific_method():
    context = sample_route_metadata()
    context["route"] = None
    context["url"] = "http://localhost:4000/posts/3/comments/10"
    context["method"] = "POST"

    endpoints = [
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
            "method": "POST",
            "route": "/posts/*/comments/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 5,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        {
            "method": "POST",
            "route": "/posts/*/comments/10",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 2,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        {
            "method": "POST",
            "route": "/posts",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 2,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
    ]

    result = match_endpoint(context, endpoints, multi=True)

    assert len(result) == 3  # Expecting two matches
    assert all(
        endpoint["endpoint"]["route"].startswith("/posts/") for endpoint in result
    )
    assert any(
        endpoint["endpoint"]["route"] == "/posts/*/comments/*" for endpoint in result
    )
    assert any(
        endpoint["endpoint"]["route"] == "/posts/*/comments/10" for endpoint in result
    )


def test_returns_no_endpoints_when_none_match():
    context = sample_route_metadata()
    context["route"] = None
    context["url"] = "http://localhost:4000/unknown/route"
    context["method"] = "GET"

    endpoints = [
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
            "method": "POST",
            "route": "/posts/*/comments/*",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 5,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
    ]

    result = match_endpoint(context, endpoints, multi=True)

    assert result == None  # Expecting no matches
