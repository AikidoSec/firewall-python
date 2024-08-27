import pytest
from .try_parse_as_json import try_parse_as_json


def test_valid_json_object():
    data = '{"key": "value"}'
    expected = {"key": "value"}
    assert try_parse_as_json(data) == expected


def test_valid_json_array():
    data = "[1, 2, 3, 4]"
    expected = [1, 2, 3, 4]
    assert try_parse_as_json(data) == expected


def test_valid_json_nested():
    data = '{"key": {"nested_key": "nested_value"}}'
    expected = {"key": {"nested_key": "nested_value"}}
    assert try_parse_as_json(data) == expected


def test_invalid_json_string():
    data = '{"key": "value"'
    assert try_parse_as_json(data) is None


def test_invalid_json_number():
    data = "123abc"
    assert try_parse_as_json(data) is None


def test_empty_string():
    data = ""
    assert try_parse_as_json(data) is None


def test_none_input():
    data = None
    assert try_parse_as_json(data) is None


def test_boolean_as_json():
    data = "true"
    expected = True
    assert try_parse_as_json(data) == expected


def test_float_as_json():
    data = "3.14"
    expected = 3.14
    assert try_parse_as_json(data) == expected


def test_json_with_special_characters():
    data = '{"key": "value with special characters !@#$%^&*()"}'
    expected = {"key": "value with special characters !@#$%^&*()"}
    assert try_parse_as_json(data) == expected
