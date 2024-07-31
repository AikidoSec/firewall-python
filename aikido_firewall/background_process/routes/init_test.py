from aikido_firewall.background_process.routes import route_to_key, Routes


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
    routes.add_route("GET", "/api/resource")
    assert len(routes.routes) == 1
    assert routes.routes["GET:/api/resource"]["hits"] == 1


def test_add_route_existing():
    routes = Routes(max_size=3)
    routes.add_route("GET", "/api/resource")
    routes.add_route("GET", "/api/resource")
    assert len(routes.routes) == 1
    assert routes.routes["GET:/api/resource"]["hits"] == 2


def test_clear_routes():
    routes = Routes(max_size=3)
    routes.add_route("GET", "/api/resource")
    routes.clear()
    assert len(routes.routes) == 0


def test_manage_routes_size_eviction():
    routes = Routes(max_size=2)
    routes.add_route("GET", "/api/resource1")
    routes.add_route("GET", "/api/resource2")
    routes.add_route("GET", "/api/resource3")  # This should evict the least used route
    assert len(routes.routes) == 2
    assert (
        "GET:/api/resource1" not in routes.routes
    )  # Assuming resource1 is the least used


def test_iterable():
    routes = Routes(max_size=3)
    routes.add_route("GET", "/api/resource1")
    routes.add_route("POST", "/api/resource2")
    routes.add_route("PUT", "/api/resource3")
    routes_list = list(routes)
    assert len(routes_list) == 3
    assert {"method": "GET", "path": "/api/resource1", "hits": 1} in routes_list
    assert {"method": "POST", "path": "/api/resource2", "hits": 1} in routes_list
    assert {"method": "PUT", "path": "/api/resource3", "hits": 1} in routes_list


def test_len():
    routes = Routes(max_size=3)
    assert len(routes) == 0
    routes.add_route("GET", "/api/resource")
    assert len(routes) == 1
    routes.add_route("POST", "/api/resource2")
    assert len(routes) == 2
