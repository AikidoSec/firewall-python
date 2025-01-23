import pytest

from . import current_context, Context
from .users import validate_user, set_user
from .. import should_block_request


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    # Make sure to reset context and cache after every test so it does not
    # interfere with other tests
    current_context.set(None)


def set_context_and_lifecycle():
    wsgi_request = {
        "REQUEST_METHOD": "GET",
        "HTTP_HEADER_1": "header 1 value",
        "HTTP_HEADER_2": "Header 2 value",
        "RANDOM_VALUE": "Random value",
        "HTTP_COOKIE": "sessionId=abc123xyz456;",
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "localhost:8080",
        "PATH_INFO": "/hello",
        "QUERY_STRING": "user=JohnDoe&age=30&age=35",
        "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": "198.51.100.23",
    }
    context = Context(
        req=wsgi_request,
        body=None,
        source="flask",
    )
    context.set_as_current_context()
    return context


def test_validate_user_valid_input():
    user = {"id": "123", "name": "Alice"}
    result = validate_user(user)
    assert result == {"id": "123", "name": "Alice"}


def test_validate_user_valid_input_with_int_id():
    user = {"id": 456, "name": "Bob"}
    result = validate_user(user)
    assert result == {"id": "456", "name": "Bob"}


def test_validate_user_missing_id(caplog):
    user = {"name": "Charlie"}
    result = validate_user(user)
    assert result is None
    assert "expects an object with 'id' property." in caplog.text


def test_validate_user_invalid_id_type(caplog):
    user = {"id": 12.34, "name": "David"}
    result = validate_user(user)
    assert result is None
    assert (
        "expects an object with 'id' property of type string or number" in caplog.text
    )


def test_validate_user_empty_string_id(caplog):
    user = {"id": "", "name": "Eve"}
    result = validate_user(user)
    assert result is None
    assert "expects an object with 'id' property non-empty string." in caplog.text


def test_validate_user_missing_name(caplog):
    user = {"id": "789"}
    result = validate_user(user)
    assert result == {"id": "789"}


def test_validate_user_empty_name(caplog):
    user = {"id": "101", "name": ""}
    result = validate_user(user)
    assert result == {"id": "101"}


def test_validate_user_invalid_user_type(caplog):
    user = ["id", "name"]
    result = validate_user(user)
    assert result is None
    assert "expects a dict with 'id' and 'name' properties" in caplog.text


def test_validate_user_invalid_user_type_dict_without_id(caplog):
    user = {"name": "Frank"}
    result = validate_user(user)
    assert result is None
    assert "expects an object with 'id' property." in caplog.text


def test_set_user_with_none(caplog):
    result = set_user(None)
    assert "expects a dict with 'id' and 'name' properties" in caplog.text


def test_set_valid_user():
    context1 = set_context_and_lifecycle()
    assert context1.user is None

    user = {"id": 456, "name": "Bob"}
    set_user(user)

    assert context1.user == {
        "id": "456",
        "name": "Bob",
        "lastIpAddress": "198.51.100.23",
    }


def test_re_set_valid_user():
    context1 = set_context_and_lifecycle()
    assert context1.user is None

    user = {"id": 456, "name": "Bob"}
    set_user(user)

    assert context1.user == {
        "id": "456",
        "name": "Bob",
        "lastIpAddress": "198.51.100.23",
    }

    user = {"id": "1000", "name": "Alice"}
    set_user(user)

    assert context1.user == {
        "id": "1000",
        "name": "Alice",
        "lastIpAddress": "198.51.100.23",
    }


def test_after_middleware(caplog):
    context1 = set_context_and_lifecycle()
    assert context1.user is None

    should_block_request()

    user = {"id": 456, "name": "Bob"}
    set_user(user)

    assert "must be called before the Zen middleware is executed" in caplog.text
    assert context1.user == {
        "id": "456",
        "name": "Bob",
        "lastIpAddress": "198.51.100.23",
    }
