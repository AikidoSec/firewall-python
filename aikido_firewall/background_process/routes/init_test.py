from aikido_firewall.background_process.routes import route_to_key


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
