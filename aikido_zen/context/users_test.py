import pytest

from .users import validate_user, set_user


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
