from aikido_zen.background_process.routes import route_to_key, Routes


class Context:
    def __init__(
        self,
        method,
        path,
        body={},
        xml={},
        content_type="application/x-www-form-urlencoded",
    ):
        self.method = method
        self.route = path
        self.body = body
        self.xml = xml
        self.headers = {"CONTENT_TYPE": content_type}


# route_to_key tests :
def test_route_to_key_get():
    assert route_to_key("GET", "/api/resource") == "GET:/api/resource"


def test_route_to_key_post():
    assert route_to_key("POST", "/api/resource") == "POST:/api/resource"


def test_route_to_key_put():
    assert route_to_key("PUT", "/api/resource") == "PUT:/api/resource"


def test_route_to_key_delete():
    assert route_to_key("DELETE", "/api/resource") == "DELETE:/api/resource"


def test_route_to_key_with_query_params():
    assert route_to_key("GET", "/api/resource?query=1") == "GET:/api/resource?query=1"


def test_route_to_key_with_trailing_slash():
    assert route_to_key("GET", "/api/resource/") == "GET:/api/resource/"


def test_route_to_key_empty_path():
    assert route_to_key("GET", "") == "GET:"


def test_initialization():
    routes = Routes(max_size=3)
    assert routes.max_size == 3
    assert routes.routes == {}


def test_add_route_new():
    routes = Routes(max_size=3)
    context1 = Context("GET", "/api/resource")
    routes.add_route(context1)
    assert len(routes.routes) == 1
    assert routes.routes["GET:/api/resource"]["hits"] == 1


def test_add_route_existing():
    routes = Routes(max_size=3)
    context1 = Context("GET", "/api/resource")

    routes.add_route(context1)
    routes.add_route(context1)
    assert len(routes.routes) == 1
    assert routes.routes["GET:/api/resource"]["hits"] == 2


def test_clear_routes():
    routes = Routes(max_size=3)
    context1 = Context("GET", "/api/resource")
    routes.add_route(context1)
    routes.clear()
    assert len(routes.routes) == 0


def test_manage_routes_size_eviction():
    routes = Routes(max_size=2)
    context1 = Context("GET", "/api/resource1")
    context2 = Context("GET", "/api/resource2")
    context3 = Context("GET", "/api/resource3")

    routes.add_route(context1)
    routes.add_route(context2)
    routes.add_route(context3)  # This should evict the least used route

    assert len(routes.routes) == 2
    assert (
        "GET:/api/resource1" not in routes.routes
    )  # Assuming resource1 is the least used


def test_iterable():
    routes = Routes(max_size=3)
    context1 = Context("GET", "/api/resource1")
    context2 = Context("POST", "/api/resource2")
    context3 = Context("PUT", "/api/resource3")

    routes.add_route(context1)
    routes.add_route(context2)
    routes.add_route(context3)

    routes_list = list(routes)
    assert len(routes_list) == 3
    assert {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 1,
        "apispec": {},
    } in routes_list
    assert {
        "method": "POST",
        "path": "/api/resource2",
        "hits": 1,
        "apispec": {},
    } in routes_list
    assert {
        "method": "PUT",
        "path": "/api/resource3",
        "hits": 1,
        "apispec": {},
    } in routes_list


def test_len():
    routes = Routes(max_size=3)
    assert len(routes) == 0

    context = Context("GET", "/api/resource")
    routes.add_route(context)
    assert len(routes) == 1

    context2 = Context("POST", "/api/resource2")
    routes.add_route(context2)
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
    routes.add_route(context1)

    routes_list = list(routes)
    assert len(routes_list) == 1
    assert {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 1,
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
            }
        },
    } in routes_list


def test_api_discovery_existing_route_empty(monkeypatch):
    routes = Routes(max_size=3)
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")
    context1 = Context("GET", "/api/resource1")
    routes.add_route(context1)
    routes_list = list(routes)

    assert {
        "method": "GET",
        "path": "/api/resource1",
        "hits": 1,
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
    routes.add_route(context2)

    routes_list = list(routes)
    assert len(routes_list) == 1
    assert {
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
                                "phone": {"type": "number"},
                            },
                            "type": "object",
                        },
                    },
                    "type": "object",
                },
                "type": "form-urlencoded",
            }
        },
    } in routes_list


def test_api_discovery_merge_routes(monkeypatch):
    routes = Routes(max_size=3)
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")
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
    routes.add_route(context1)
    routes.add_route(context2)

    routes_list = list(routes)
    assert len(routes_list) == 1
    assert {
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
        },
    } in routes_list
