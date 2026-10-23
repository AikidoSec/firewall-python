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


def test_it_prefers_specific_method_over_wildcard_first_case():
    result = match_endpoints(
        sample_route_metadata(
            url="http://localhost:4000/api/test", route="/api/test", method="POST"
        ),
        [
            {
                "method": "*",
                "route": "/api/test",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 20,
                    "windowSizeInMS": 60000,
                },
            },
            {
                "method": "POST",
                "route": "/api/test",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 100,
                    "windowSizeInMS": 60000,
                },
            },
        ],
    )

    expected = {
        "method": "POST",
        "route": "/api/test",
        "forceProtectionOff": False,
        "rateLimiting": {
            "enabled": True,
            "maxRequests": 100,
            "windowSizeInMS": 60000,
        },
    }

    assert result[0] == expected


def test_it_prefers_specific_method_over_wildcard_second_case():
    result = match_endpoints(
        sample_route_metadata(
            url="http://localhost:4000/api/test", route="/api/test", method="POST"
        ),
        [
            {
                "method": "POST",
                "route": "/api/test",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 100,
                    "windowSizeInMS": 60000,
                },
            },
            {
                "method": "*",
                "route": "/api/test",
                "forceProtectionOff": False,
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 20,
                    "windowSizeInMS": 60000,
                },
            },
        ],
    )

    expected = {
        "method": "POST",
        "route": "/api/test",
        "forceProtectionOff": False,
        "rateLimiting": {
            "enabled": True,
            "maxRequests": 100,
            "windowSizeInMS": 60000,
        },
    }

    assert result[0] == expected


@pytest.mark.parametrize("route", ["/api/[/*", "/api/(/*", "/api/v1+?+/*"])
def test_invalid_wildcard_route_is_skipped(route):
    endpoints = [
        {"method": "POST", "route": route, "forceProtectionOff": True},
        {"method": "POST", "route": "/api/*", "forceProtectionOff": False},
    ]
    assert match_endpoints(
        sample_route_metadata(route=None, url="/api/[/x"), endpoints
    ) == [endpoints[1]]


def test_wildcard_route_keeps_regex_characters_that_compile():
    endpoints = [{"method": "POST", "route": "/v1.0/*", "forceProtectionOff": False}]
    for url in ["/v1.0/abc", "/v1x0/abc"]:
        assert (
            match_endpoints(sample_route_metadata(route=None, url=url), endpoints)
            == endpoints
        )


def test_wildcard_route_is_compiled_once(monkeypatch):
    endpoints = [
        {"method": "POST", "route": "/compiled-once/*", "forceProtectionOff": False}
    ]
    route_metadata = sample_route_metadata(route=None, url="/compiled-once/x")
    assert match_endpoints(route_metadata, endpoints) == endpoints

    def fail_to_compile(*args):
        raise AssertionError("compiled the route again")

    monkeypatch.setattr(
        "aikido_zen.helpers.match_endpoints.re.compile", fail_to_compile
    )
    for _ in range(3):
        assert match_endpoints(route_metadata, endpoints) == endpoints


def test_invalid_wildcard_route_is_logged_once(caplog):
    endpoints = [{"method": "POST", "route": "/logged-once/[/*"}]
    route_metadata = sample_route_metadata(route=None, url="/logged-once/x")
    for _ in range(3):
        assert match_endpoints(route_metadata, endpoints) is None
    warnings = [r for r in caplog.records if "/logged-once/[/*" in r.getMessage()]
    assert len(warnings) == 1
    assert warnings[0].levelname == "WARNING"
