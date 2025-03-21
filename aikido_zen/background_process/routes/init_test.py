from aikido_zen.background_process.routes import Routes
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


def gen_route_metadata(method="GET", route="/test", url="http://localhost:5000"):
    return {"method": method, "route": route, "url": url}


def test_initialization():
    routes = Routes(max_size=3)
    assert routes.max_size == 3
    assert routes.routes == {}


def test_get_route():
    routes = Routes(max_size=3)

    routes.initialize_route(gen_route_metadata(method="GET", route="/api/resource1"))
    routes.increment_route(gen_route_metadata(method="GET", route="/api/resource1"))

    routes.initialize_route(gen_route_metadata(method="POST", route="/api/resource2"))
    routes.increment_route(gen_route_metadata(method="POST", route="/api/resource2"))

    routes.initialize_route(gen_route_metadata(method="PUT", route="/api/resource3"))
    routes.increment_route(gen_route_metadata(method="PUT", route="/api/resource3"))

    assert routes.get(gen_route_metadata(method="GET", route="/api/resource1")) == {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 1,
        "hits_delta_since_sync": 1,
        "apispec": {},
    }
    assert routes.get(gen_route_metadata(method="POST", route="/api/resource2")) == {
        "method": "POST",
        "path": "/api/resource2",
        "hits": 1,
        "hits_delta_since_sync": 1,
        "apispec": {},
    }
    assert routes.get(gen_route_metadata(method="PUT", route="/api/resource3")) == {
        "method": "PUT",
        "path": "/api/resource3",
        "hits": 1,
        "hits_delta_since_sync": 1,
        "apispec": {},
    }
    assert routes.get(gen_route_metadata(method="GE", route="/api/resource1")) == None
    assert routes.get(gen_route_metadata(method="GET", route="/api/resource")) == None


def test_initialize_route():
    routes = Routes(max_size=3)
    routes.initialize_route(gen_route_metadata(route="/api/resource"))
    assert len(routes.routes) == 1
    assert routes.routes["GET:/api/resource"]["hits"] == 0

    # Make sure does not do anything if route does not exist
    routes.initialize_route(gen_route_metadata(route="/api/resource"))
    assert len(routes.routes) == 1
    assert routes.routes["GET:/api/resource"]["hits"] == 0


def test_increment_route():
    routes = Routes(max_size=3)

    routes.initialize_route(gen_route_metadata(route="/api/resource"))
    routes.increment_route(gen_route_metadata(route="/api/resource"))
    assert len(routes.routes) == 1
    assert routes.routes["GET:/api/resource"]["hits"] == 1


def test_increment_route_twice():
    routes = Routes(max_size=3)

    routes.initialize_route(gen_route_metadata(route="/api/resource"))
    routes.increment_route(gen_route_metadata(route="/api/resource"))
    routes.increment_route(gen_route_metadata(route="/api/resource"))
    assert len(routes.routes) == 1
    assert routes.routes["GET:/api/resource"]["hits"] == 2


def test_clear_routes():
    routes = Routes(max_size=3)
    routes.initialize_route(gen_route_metadata(route="/api/resource"))
    routes.clear()
    assert len(routes.routes) == 0


def test_manage_routes_size_eviction():
    routes = Routes(max_size=2)

    routes.initialize_route(gen_route_metadata(route="/api/resource1"))
    routes.initialize_route(gen_route_metadata(route="/api/resource2"))
    routes.initialize_route(
        gen_route_metadata(route="/api/resource3")
    )  # This should evict the least used route

    assert len(routes.routes) == 2
    assert (
        "GET:/api/resource1" not in routes.routes
    )  # Assuming resource1 is the least used


def test_iterable():
    routes = Routes(max_size=3)

    routes.initialize_route(gen_route_metadata(method="GET", route="/api/resource1"))
    routes.initialize_route(gen_route_metadata(method="POST", route="/api/resource2"))
    routes.initialize_route(gen_route_metadata(method="PUT", route="/api/resource3"))

    routes_list = list(routes)
    assert len(routes_list) == 3
    assert {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 0,
        "hits_delta_since_sync": 0,
        "apispec": {},
    } in routes_list
    assert {
        "method": "POST",
        "path": "/api/resource2",
        "hits": 0,
        "hits_delta_since_sync": 0,
        "apispec": {},
    } in routes_list
    assert {
        "method": "PUT",
        "path": "/api/resource3",
        "hits": 0,
        "hits_delta_since_sync": 0,
        "apispec": {},
    } in routes_list


def test_len():
    routes = Routes(max_size=3)
    assert len(routes) == 0

    routes.initialize_route(gen_route_metadata(route="/api/resource"))
    assert len(routes) == 1

    routes.initialize_route(gen_route_metadata(method="POST", route="/api/resource2"))
    assert len(routes) == 2


def test_api_discovery_for_new_routes(monkeypatch):
    routes = Routes(max_size=3)
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")
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
    routes.initialize_route(gen_route_metadata(route="/api/resource1"))

    routes_list = list(routes)
    assert len(routes_list) == 1
    assert {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 0,
        "hits_delta_since_sync": 0,
        "apispec": {},
    } in routes_list

    apispec = get_api_info(context1)
    routes.update_route_with_apispec(
        gen_route_metadata(route="/api/resource1"), apispec
    )

    routes_list = list(routes)
    assert len(routes_list) == 1
    assert {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 0,
        "hits_delta_since_sync": 0,
        "apispec": apispec,
    } in routes_list


def test_api_discovery_existing_route_empty(monkeypatch):
    routes = Routes(max_size=3)
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")
    route_metadata = gen_route_metadata(route="/api/resource1")

    context1 = Context("GET", "/api/resource1")
    routes.initialize_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context1))
    routes_list = list(routes)
    assert {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 0,
        "hits_delta_since_sync": 0,
        "apispec": {},
    } in routes_list

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
    routes.increment_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context2))

    routes_list = list(routes)
    assert len(routes_list) == 1
    assert {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 1,
        "hits_delta_since_sync": 1,
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
                                "phone": {"type": "number"},
                            },
                            "type": "object",
                        },
                    },
                    "type": "object",
                },
                "type": "form-urlencoded",
            },
            "auth": None,
            "query": None,
        },
    } in routes_list


def test_api_discovery_merge_routes(monkeypatch):
    routes = Routes(max_size=3)
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")
    route_metadata = gen_route_metadata(route="/api/resource1")

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
    routes.initialize_route(route_metadata)
    routes.increment_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context1))
    routes.increment_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context2))

    routes_list = list(routes)
    assert len(routes_list) == 1
    assert {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 2,
        "hits_delta_since_sync": 2,
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
    } in routes_list


def test_merge_body_schema(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")

    routes = Routes(200)
    assert list(routes) == []

    routes.initialize_route(gen_route_metadata(method="POST", route="/body"))
    routes.increment_route(gen_route_metadata(method="POST", route="/body"))
    assert list(routes) == [
        {
            "method": "POST",
            "path": "/body",
            "hits": 1,
            "hits_delta_since_sync": 1,
            "apispec": {},
        },
    ]

    context1 = Context(
        "POST",
        "/body",
        {"test": "abc", "arr": [1, 2, 3], "sub": {"y": 123}},
    )
    route_metadata1 = gen_route_metadata(method="POST", route="/body")
    routes.increment_route(route_metadata1)
    routes.update_route_with_apispec(route_metadata1, get_api_info(context1))
    assert list(routes) == [
        {
            "method": "POST",
            "path": "/body",
            "hits": 2,
            "hits_delta_since_sync": 2,
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
    ]

    context2 = Context(
        "POST",
        "/body",
        {"test": "abc", "arr": [1, 2, 3], "test2": 1, "sub": {"x": 123}},
    )
    routes.increment_route(route_metadata1)
    routes.update_route_with_apispec(route_metadata1, get_api_info(context2))
    routes.increment_route(route_metadata1)
    assert list(routes) == [
        {
            "method": "POST",
            "path": "/body",
            "hits": 4,
            "hits_delta_since_sync": 4,
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
    ]


def test_add_query_schema(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")

    routes = Routes(200)
    context = Context("GET", "/query", None, query={"test": "abc", "t": "123"})
    route_metadata = gen_route_metadata(route="/query")

    routes.initialize_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context))

    assert list(routes) == [
        {
            "method": "GET",
            "path": "/query",
            "hits": 0,
            "hits_delta_since_sync": 0,
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
    ]


def test_merge_query_schema(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")

    routes = Routes(200)
    assert list(routes) == []
    route_metadata = gen_route_metadata(route="/query")
    routes.initialize_route(route_metadata)
    routes.increment_route(route_metadata)
    assert list(routes) == [
        {
            "method": "GET",
            "path": "/query",
            "hits": 1,
            "hits_delta_since_sync": 1,
            "apispec": {},
        },
    ]
    context1 = Context("GET", "/query", None, query={"test": "abc"})
    context2 = Context("GET", "/query", None, query={"x": "123", "test": "abc"})

    routes.increment_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context1))

    routes.increment_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context2))

    routes.increment_route(route_metadata)

    assert list(routes) == [
        {
            "method": "GET",
            "path": "/query",
            "hits": 4,
            "hits_delta_since_sync": 4,
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
    ]


def test_add_auth_schema(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")

    routes = Routes(200)
    route_metadata1 = gen_route_metadata(route="/auth")
    context1 = Context("GET", "/auth", headers={"AUTHORIZATION": "Bearer token"})
    route_metadata2 = gen_route_metadata(route="/auth2")
    context2 = Context("GET", "/auth2", cookies={"session": "test"})
    route_metadata3 = gen_route_metadata(route="/auth3")
    context3 = Context("GET", "/auth3", headers={"X_API_KEY": "token"})

    routes.initialize_route(route_metadata1)
    routes.update_route_with_apispec(route_metadata1, get_api_info(context1))
    routes.initialize_route(route_metadata2)
    routes.update_route_with_apispec(route_metadata2, get_api_info(context2))
    routes.initialize_route(route_metadata3)
    routes.update_route_with_apispec(route_metadata3, get_api_info(context3))

    assert list(routes) == [
        {
            "method": "GET",
            "path": "/auth",
            "hits": 0,
            "hits_delta_since_sync": 0,
            "apispec": {
                "body": None,
                "query": None,
                "auth": [{"type": "http", "scheme": "bearer"}],
            },
        },
        {
            "method": "GET",
            "path": "/auth2",
            "hits": 0,
            "hits_delta_since_sync": 0,
            "apispec": {
                "body": None,
                "query": None,
                "auth": [{"type": "apiKey", "in": "cookie", "name": "session"}],
            },
        },
        {
            "method": "GET",
            "path": "/auth3",
            "hits": 0,
            "hits_delta_since_sync": 0,
            "apispec": {
                "body": None,
                "query": None,
                "auth": [{"type": "apiKey", "in": "header", "name": "x-api-key"}],
            },
        },
    ]


def test_merge_auth_schema(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")

    routes = Routes(200)
    assert list(routes) == []
    route_metadata = gen_route_metadata(route="/auth")

    routes.initialize_route(route_metadata)
    routes.increment_route(route_metadata)

    context1 = Context("GET", "/auth", headers={"AUTHORIZATION": "Bearer token"})
    routes.increment_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context1))

    context2 = Context("GET", "/auth", headers={"AUTHORIZATION": "Basic token"})
    routes.increment_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context2))

    context3 = Context("GET", "/auth", headers={"X_API_KEY": "token"})
    routes.increment_route(route_metadata)
    routes.update_route_with_apispec(route_metadata, get_api_info(context3))
    routes.increment_route(route_metadata)

    assert list(routes)[0] == {
        "method": "GET",
        "path": "/auth",
        "hits": 5,
        "hits_delta_since_sync": 5,
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
    assert len(list(routes)) == 1
