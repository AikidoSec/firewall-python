import pytest

from .is_same_type import is_same_type


def test_is_same_type_single_primitives():
    assert is_same_type("string", "string") is True
    assert is_same_type("number", "number") is True
    assert is_same_type("boolean", "boolean") is True
    assert is_same_type("string", "number") is False
    assert is_same_type("object", "array") is False


def test_is_same_type_single_and_array():
    assert is_same_type("string", ["string"]) is True
    assert is_same_type(["string"], "string") is True
    assert is_same_type("number", ["number"]) is True
    assert is_same_type(["number"], "number") is True
    assert is_same_type("string", ["number"]) is False
    assert is_same_type(["string"], "number") is False


def test_is_same_type_multiple_primitives():
    assert is_same_type(["string", "number"], ["number", "string"]) is True
    assert is_same_type(["string", "boolean"], ["boolean", "string"]) is True
    assert is_same_type(["string", "number"], ["string", "number"]) is True
    assert is_same_type(["string"], ["string", "number"]) is False
    assert is_same_type(["string", "number"], ["string"]) is False


def test_is_same_type_different_length_arrays():
    assert is_same_type(["string", "number"], ["string"]) is False
    assert is_same_type(["string"], ["string", "number"]) is False
    assert is_same_type(["string", "number"], ["string", "number", "boolean"]) is False


def test_is_same_type_empty_arrays():
    assert is_same_type([], []) is True
    assert is_same_type([], ["string"]) is False
    assert is_same_type(["string"], []) is False


def test_is_same_type_non_list_input():
    assert is_same_type("string", "string") is True
    assert is_same_type("string", "object") is False
    assert is_same_type("string", ["object"]) is False
    assert is_same_type(["string"], "object") is False


def test_is_same_type_mixed_types():
    assert is_same_type(["string", "number"], ["number", "string"]) is True
    assert is_same_type(["string", "object"], ["object", "string"]) is True
    assert is_same_type(["string", "number"], ["string", "object"]) is False
    assert is_same_type(["object"], ["string"]) is False


def test_is_same_type_with_none():
    assert is_same_type(None, None) is True
    assert is_same_type(None, "string") is False
    assert is_same_type("string", None) is False
    assert is_same_type(None, ["string"]) is False
    assert is_same_type(["string"], None) is False
