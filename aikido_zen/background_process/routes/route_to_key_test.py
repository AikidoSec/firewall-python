import pytest
from .route_to_key import route_to_key


def gen_route_metadata(method="GET", route="/test", url="http://localhost:5000"):
    return {"method": method, "route": route, "url": url}


def test_route_to_key_get():
    assert (
        route_to_key(gen_route_metadata(method="GET", route="/api/resource"))
        == "GET:/api/resource"
    )


def test_route_to_key_post():
    assert (
        route_to_key(gen_route_metadata(method="POST", route="/api/resource"))
        == "POST:/api/resource"
    )


def test_route_to_key_put():
    assert (
        route_to_key(gen_route_metadata(method="PUT", route="/api/resource"))
        == "PUT:/api/resource"
    )


def test_route_to_key_delete():
    assert (
        route_to_key(gen_route_metadata(method="DELETE", route="/api/resource"))
        == "DELETE:/api/resource"
    )


def test_route_to_key_with_query_params():
    assert (
        route_to_key(gen_route_metadata(method="GET", route="/api/resource?query=1"))
        == "GET:/api/resource?query=1"
    )


def test_route_to_key_with_trailing_slash():
    assert (
        route_to_key(gen_route_metadata(method="GET", route="/api/resource/"))
        == "GET:/api/resource/"
    )


def test_route_to_key_empty_path():
    assert route_to_key(gen_route_metadata(method="GET", route="")) == "GET:"
