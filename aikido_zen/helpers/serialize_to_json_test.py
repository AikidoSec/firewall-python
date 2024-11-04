import pytest
from .serialize_to_json import serialize_to_json


def test_serialize_basic_types():
    assert serialize_to_json({"key": "value"}) == '{"key": "value"}'
    assert serialize_to_json(["item1", "item2"]) == '["item1", "item2"]'
    assert serialize_to_json(123) == "123"
    assert serialize_to_json(45.67) == "45.67"
    assert serialize_to_json(True) == "true"
    assert serialize_to_json(None) == "null"


def test_serialize_complex_types():
    class CustomObject:
        def __init__(self, name):
            self.name = name

    obj = CustomObject("test")
    assert serialize_to_json(obj) == "{}"


def test_serialize_dict_with_non_serializable_key():
    obj = {object(): "value"}
    assert serialize_to_json(obj) == "{}"


def test_serialize_list_with_non_serializable_item():
    obj = [1, 2, object()]
    assert serialize_to_json(obj) == "{}"


def test_serialize_nested_structures():
    obj = {"key": ["value1", {"nested_key": "nested_value"}]}
    assert (
        serialize_to_json(obj) == '{"key": ["value1", {"nested_key": "nested_value"}]}'
    )


def test_serialize_empty_input():
    assert serialize_to_json("") == '""'
    assert serialize_to_json([]) == "[]"
    assert serialize_to_json({}) == "{}"


def test_serialize_non_serializable_object():
    class NonSerializable:
        pass

    obj = NonSerializable()
    assert serialize_to_json(obj) == "{}"
