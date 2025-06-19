import pytest

from aikido_zen.storage.routes import Routes
from aikido_zen.api_discovery.get_api_info import get_api_info


class Context:
    def __init__(
        self,
        method,
        path,
        body={},
        xml={},
        content_type="application/x-www-form-urlencoded",
        headers={},
        query={},
        cookies={},
    ):
        self.method = method
        self.route = path
        self.body = body
        self.xml = xml
        self.headers = headers
        self.headers["CONTENT_TYPE"] = content_type
        self.query = query
        self.cookies = cookies


def test_init_default_max_size():
    routes = Routes()
    assert routes.max_size == 1000
    assert routes.routes == {}


def test_init_custom_max_size():
    routes = Routes(max_size=500)
    assert routes.max_size == 500
    assert routes.routes == {}


def test_get_existing_route():
    routes = Routes()
    routes.routes = {"GET:/test": {"method": "GET", "path": "/test"}}

    result = routes.get("GET", "/test")
    assert result == {"method": "GET", "path": "/test"}


def test_get_nonexistent_route():
    routes = Routes()

    assert routes.get("GET", "/nonexistent") is None


def test_ensure_route_creates_new_route():
    routes = Routes()

    routes.ensure_route("POST", "/api/test")

    assert routes.get("POST", "/api/test") == {
        "method": "POST",
        "path": "/api/test",
        "hits": 0,
        "apispec": {},
    }


def test_ensure_route_existing_route_returns_early():
    routes = Routes()
    routes.routes = {"GET:/test": {"method": "GET", "path": "/test", "hits": 5}}

    routes.ensure_route("GET", "/test")

    assert routes.get("GET", "/test")["hits"] == 5
    assert routes.export() == {
        "GET:/test": {"hits": 5, "method": "GET", "path": "/test"}
    }


def test_increment_route_new_route():
    routes = Routes()

    routes.increment_route("GET", "/test")

    assert routes.get("GET", "/test")["hits"] == 1


def test_increment_route_existing_route():
    routes = Routes()

    routes.increment_route("GET", "/test")
    routes.increment_route("GET", "/test")
    routes.increment_route("GET", "/test")
    routes.increment_route("GET", "/test")
    routes.increment_route("GET", "/test")
    routes.increment_route("GET", "/test")

    assert routes.get("GET", "/test")["hits"] == 6
    assert routes.export()["GET:/test"] == {
        "apispec": {},
        "hits": 6,
        "method": "GET",
        "path": "/test",
    }


def test_increment_route_multiple_times():
    routes = Routes()

    routes.increment_route("POST", "/api/data")
    routes.increment_route("POST", "/api/data")
    routes.increment_route("POST", "/api/data")
    routes.increment_route("GET", "/api/data")

    assert routes.get("POST", "/api/data")["hits"] == 3
    assert routes.get("GET", "/api/data")["hits"] == 1


def test_get_route():
    routes = Routes(max_size=3)

    # Use ensure_route instead of initialize_route
    routes.ensure_route(method="GET", route="/api/resource1")
    routes.increment_route(method="GET", route="/api/resource1")

    routes.ensure_route(method="POST", route="/api/resource2")
    routes.increment_route(method="POST", route="/api/resource2")

    routes.ensure_route(method="PUT", route="/api/resource3")
    routes.increment_route(method="PUT", route="/api/resource3")

    # Update assertions to match the current structure
    assert routes.get(method="GET", route="/api/resource1") == {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 1,
        "apispec": {},
    }
    assert routes.get(method="POST", route="/api/resource2") == {
        "method": "POST",
        "path": "/api/resource2",
        "hits": 1,
        "apispec": {},
    }
    assert routes.get(method="PUT", route="/api/resource3") == {
        "method": "PUT",
        "path": "/api/resource3",
        "hits": 1,
        "apispec": {},
    }
    assert routes.get(method="GE", route="/api/resource1") is None
    assert routes.get(method="GET", route="/api/resource") is None


def test_ensure_route():
    routes = Routes(max_size=3)
    routes.ensure_route(method="GET", route="/api/resource")
    assert len(routes.export()) == 1
    assert routes.get(method="GET", route="/api/resource")["hits"] == 0

    # Ensure it does not add the route again if it already exists
    routes.ensure_route(method="GET", route="/api/resource")
    assert len(routes.export()) == 1
    assert routes.get(method="GET", route="/api/resource")["hits"] == 0


def test_increment_route():
    routes = Routes(max_size=3)

    routes.ensure_route(method="GET", route="/api/resource")
    routes.increment_route(method="GET", route="/api/resource")
    assert len(routes.export()) == 1
    assert routes.get(method="GET", route="/api/resource")["hits"] == 1


def test_increment_route_twice():
    routes = Routes(max_size=3)

    routes.ensure_route(method="GET", route="/api/resource")
    routes.increment_route(method="GET", route="/api/resource")
    routes.increment_route(method="GET", route="/api/resource")

    assert len(routes.export()) == 1
    assert routes.get(method="GET", route="/api/resource")["hits"] == 2


def test_clear_routes():
    routes = Routes(max_size=3)
    routes.ensure_route(method="GET", route="/api/resource")
    routes.clear()
    assert routes.empty()


def test_manage_routes_size_eviction():
    routes = Routes(max_size=2)

    routes.ensure_route(method="GET", route="/api/resource1")
    routes.ensure_route(method="GET", route="/api/resource2")
    routes.ensure_route(method="GET", route="/api/resource3")

    assert len(routes.export()) == 2
    assert routes.get(method="GET", route="/api/resource1") is None


def test_api_discovery_for_new_routes(monkeypatch):
    routes = Routes(max_size=3)

    context1 = Context(
        "GET",
        "/api/resource1",
        body={
            "user": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": 12345678,
            },
        },
    )

    # Ensure route is initialized
    routes.ensure_route(method="GET", route="/api/resource1")

    # Check if the route is correctly added
    routes_export = routes.export()
    assert len(routes_export) == 1
    assert routes_export["GET:/api/resource1"] == {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 0,
        "apispec": {},
    }

    routes.update_route_with_apispec(
        method="GET", route="/api/resource1", apispec=get_api_info(context1)
    )

    # Verify the route is updated with apispec
    routes_export = routes.export()
    assert len(routes_export) == 1
    assert routes_export["GET:/api/resource1"]["apispec"] == {
        "auth": None,
        "body": {
            "schema": {
                "properties": {
                    "user": {
                        "properties": {
                            "email": {"type": "string"},
                            "name": {"type": "string"},
                            "phone": {"type": "number"},
                        },
                        "type": "object",
                    }
                },
                "type": "object",
            },
            "type": "form-urlencoded",
        },
        "query": None,
    }


def test_api_discovery_for_new_routes_without_ensure_route(monkeypatch):
    routes = Routes(max_size=3)

    context1 = Context(
        "GET",
        "/api/resource1",
        body={
            "user": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": 12345678,
            },
        },
    )
    routes.update_route_with_apispec(
        method="GET", route="/api/resource1", apispec=get_api_info(context1)
    )

    # Verify the route is updated with apispec
    routes_export = routes.export()
    assert len(routes_export) == 1
    assert routes_export["GET:/api/resource1"]["apispec"] == {
        "auth": None,
        "body": {
            "schema": {
                "properties": {
                    "user": {
                        "properties": {
                            "email": {"type": "string"},
                            "name": {"type": "string"},
                            "phone": {"type": "number"},
                        },
                        "type": "object",
                    }
                },
                "type": "object",
            },
            "type": "form-urlencoded",
        },
        "query": None,
    }


def test_api_discovery_existing_route_empty(monkeypatch):
    routes = Routes(max_size=3)

    context1 = Context("GET", "/api/resource1")
    # Update route with empty apispec
    routes.update_route_with_apispec(method="GET", route="/api/resource1", apispec={})

    # Verify the route is correctly added with empty apispec
    routes_export = routes.export()
    assert "GET:/api/resource1" in routes_export
    assert routes_export["GET:/api/resource1"]["apispec"] == {}

    # Mock context with body
    context2 = Context(
        "GET",
        "/api/resource1",
        body={
            "user": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": 12345678,
            },
        },
    )

    # Increment route hit count and update apispec
    routes.increment_route(method="GET", route="/api/resource1")
    routes.update_route_with_apispec(
        method="GET", route="/api/resource1", apispec=get_api_info(context2)
    )

    # Verify the route is updated with new apispec and hit count
    routes_export = routes.export()
    assert len(routes_export) == 1
    assert routes_export["GET:/api/resource1"] == {
        "apispec": {
            "auth": None,
            "body": {
                "schema": {
                    "properties": {
                        "user": {
                            "properties": {
                                "email": {"type": "string"},
                                "name": {"type": "string"},
                                "phone": {"type": "number"},
                            },
                            "type": "object",
                        }
                    },
                    "type": "object",
                },
                "type": "form-urlencoded",
            },
            "query": None,
        },
        "hits": 1,
        "method": "GET",
        "path": "/api/resource1",
    }


def test_api_discovery_merge_routes(monkeypatch):
    routes = Routes(max_size=3)

    context1 = Context(
        "GET",
        "/api/resource1",
        body={"user": {"name": "John Doe", "email": "john.doe@example.com", "age": 20}},
    )
    context2 = Context(
        "GET",
        "/api/resource1",
        body={
            "user": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": 12345678,
            },
        },
        content_type="application/json",
    )
    routes.increment_route("GET", "/api/resource1")
    routes.update_route_with_apispec("GET", "/api/resource1", get_api_info(context1))
    routes.increment_route("GET", "/api/resource1")
    routes.update_route_with_apispec("GET", "/api/resource1", get_api_info(context2))

    routes_list = routes.export()
    assert len(routes_list) == 1
    assert routes_list["GET:/api/resource1"] == {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 2,
        "apispec": {
            "body": {
                "schema": {
                    "properties": {
                        "user": {
                            "properties": {
                                "email": {
                                    "type": "string",
                                },
                                "name": {
                                    "type": "string",
                                },
                                "phone": {"type": "number", "optional": True},
                                "age": {"type": "number", "optional": True},
                            },
                            "type": "object",
                        },
                    },
                    "type": "object",
                },
                "type": "json",
            },
            "auth": None,
            "query": None,
        },
    }


def test_merge_body_schema(monkeypatch):
    routes = Routes(200)
    assert len(routes.export()) == 0

    routes.increment_route("POST", "/body")
    assert routes.export() == {
        "POST:/body": {
            "method": "POST",
            "path": "/body",
            "hits": 1,
            "apispec": {},
        },
    }

    context1 = Context(
        "POST",
        "/body",
        {"test": "abc", "arr": [1, 2, 3], "sub": {"y": 123}},
    )

    routes.update_route_with_apispec("POST", "/body", get_api_info(context1))
    assert routes.export() == {
        "POST:/body": {
            "method": "POST",
            "path": "/body",
            "hits": 1,
            "apispec": {
                "body": {
                    "type": "form-urlencoded",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "test": {"type": "string"},
                            "arr": {
                                "type": "array",
                                "items": {"type": "number"},
                            },
                            "sub": {
                                "type": "object",
                                "properties": {
                                    "y": {"type": "number"},
                                },
                            },
                        },
                    },
                },
                "auth": None,
                "query": None,
            },
        },
    }

    context2 = Context(
        "POST",
        "/body",
        {"test": "abc", "arr": [1, 2, 3], "test2": 1, "sub": {"x": 123}},
    )
    routes.increment_route("POST", "/body")
    routes.update_route_with_apispec("POST", "/body", get_api_info(context2))
    routes.increment_route("POST", "/body")
    assert routes.export() == {
        "POST:/body": {
            "method": "POST",
            "path": "/body",
            "hits": 3,
            "apispec": {
                "body": {
                    "type": "form-urlencoded",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "test": {"type": "string"},
                            "arr": {
                                "type": "array",
                                "items": {"type": "number"},
                            },
                            "sub": {
                                "type": "object",
                                "properties": {
                                    "y": {"type": "number", "optional": True},
                                    "x": {"type": "number", "optional": True},
                                },
                            },
                            "test2": {"type": "number", "optional": True},
                        },
                    },
                },
                "auth": None,
                "query": None,
            },
        },
    }


def test_add_query_schema(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")

    routes = Routes(200)
    context = Context("GET", "/query", None, query={"test": "abc", "t": "123"})

    routes.update_route_with_apispec("GET", "/query", get_api_info(context))

    assert routes.export() == {
        "GET:/query": {
            "method": "GET",
            "path": "/query",
            "hits": 0,
            "apispec": {
                "body": None,
                "auth": None,
                "query": {
                    "type": "object",
                    "properties": {
                        "test": {"type": "string"},
                        "t": {"type": "string"},
                    },
                },
            },
        },
    }


def test_merge_query_schema(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")

    routes = Routes(200)
    assert len(routes.export()) == 0
    routes.increment_route("GET", "/query")
    assert list(routes.export().values()) == [
        {
            "method": "GET",
            "path": "/query",
            "hits": 1,
            "apispec": {},
        },
    ]
    context1 = Context("GET", "/query", None, query={"test": "abc"})
    context2 = Context("GET", "/query", None, query={"x": "123", "test": "abc"})

    routes.increment_route("GET", "/query")
    routes.update_route_with_apispec("GET", "/query", get_api_info(context1))

    routes.increment_route("GET", "/query")
    routes.update_route_with_apispec("GET", "/query", get_api_info(context2))

    routes.increment_route("GET", "/query")

    assert routes.export() == {
        "GET:/query": {
            "method": "GET",
            "path": "/query",
            "hits": 4,
            "apispec": {
                "query": {
                    "type": "object",
                    "properties": {
                        "test": {"type": "string"},
                        "x": {"type": "string", "optional": True},
                    },
                },
                "auth": None,
                "body": None,
            },
        },
    }


def test_add_auth_schema(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")

    routes = Routes(200)
    context1 = Context("GET", "/auth", headers={"AUTHORIZATION": "Bearer token"})
    context2 = Context("GET", "/auth2", cookies={"session": "test"})
    context3 = Context("GET", "/auth3", headers={"X_API_KEY": "token"})

    routes.update_route_with_apispec("GET", "/auth", get_api_info(context1))
    routes.update_route_with_apispec("GET", "/auth2", get_api_info(context2))
    routes.update_route_with_apispec("GET", "/auth3", get_api_info(context3))

    assert routes.export() == {
        "GET:/auth": {
            "method": "GET",
            "path": "/auth",
            "hits": 0,
            "apispec": {
                "body": None,
                "query": None,
                "auth": [{"type": "http", "scheme": "bearer"}],
            },
        },
        "GET:/auth2": {
            "method": "GET",
            "path": "/auth2",
            "hits": 0,
            "apispec": {
                "body": None,
                "query": None,
                "auth": [{"type": "apiKey", "in": "cookie", "name": "session"}],
            },
        },
        "GET:/auth3": {
            "method": "GET",
            "path": "/auth3",
            "hits": 0,
            "apispec": {
                "body": None,
                "query": None,
                "auth": [{"type": "apiKey", "in": "header", "name": "x-api-key"}],
            },
        },
    }


def test_merge_auth_schema(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")

    routes = Routes(200)
    assert routes.empty()

    routes.increment_route("GET", "/auth")

    context1 = Context("GET", "/auth", headers={"AUTHORIZATION": "Bearer token"})
    routes.increment_route("GET", "/auth")
    routes.update_route_with_apispec("GET", "/auth", get_api_info(context1))

    context2 = Context("GET", "/auth", headers={"AUTHORIZATION": "Basic token"})
    routes.increment_route("GET", "/auth")
    routes.update_route_with_apispec("GET", "/auth", get_api_info(context2))

    context3 = Context("GET", "/auth", headers={"X_API_KEY": "token"})
    routes.increment_route("GET", "/auth")
    routes.update_route_with_apispec("GET", "/auth", get_api_info(context3))
    routes.increment_route("GET", "/auth")

    assert routes.export()["GET:/auth"] == {
        "method": "GET",
        "path": "/auth",
        "hits": 5,
        "apispec": {
            "auth": [
                {"type": "http", "scheme": "bearer"},
                {"type": "http", "scheme": "basic"},
                {"type": "apiKey", "in": "header", "name": "x-api-key"},
            ],
            "body": None,
            "query": None,
        },
    }
    assert len(routes.export()) == 1
