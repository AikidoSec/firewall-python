import pytest
from .merge_types import merge_types


def test_merge_types_with_primitive_types():
    schema1 = {"type": ["string", "number"]}
    schema2 = {"type": ["number", "boolean"]}
    expected = {"string", "number", "boolean"}
    assert set(merge_types(schema1, schema2)["type"]) == expected


def test_merge_types_with_same_types():
    schema1 = {"type": ["string"]}
    schema2 = {"type": ["string"]}
    expected = {"string"}
    assert set(merge_types(schema1, schema2)["type"]) == expected


def test_merge_types_with_different_single_types():
    schema1 = {"type": "string"}
    schema2 = {"type": "number"}
    expected = {"string", "number"}
    assert set(merge_types(schema1, schema2)["type"]) == expected


def test_merge_types_with_null_type():
    schema1 = {"type": "null"}
    schema2 = {"type": ["string"]}
    expected = {"string", "null"}
    assert set(merge_types(schema1, schema2)["type"]) == expected


def test_merge_types_with_non_primitive_type():
    schema1 = {"type": ["object"]}
    schema2 = {"type": ["string"]}
    expected = {"object"}  # Non-primitive type takes precedence
    assert set(merge_types(schema1, schema2)["type"]) == expected


def test_merge_types_with_both_non_primitive_types():
    schema1 = {"type": ["object"]}
    schema2 = {"type": ["array"]}
    expected = {"object"}  # Non-primitive type takes precedence
    assert set(merge_types(schema1, schema2)["type"]) == expected


def test_merge_types_with_empty_schema():
    schema1 = {"type": []}
    schema2 = {"type": ["string"]}
    expected = {"string"}
    assert set(merge_types(schema1, schema2)["type"]) == expected


def test_merge_types_with_empty_and_null_schema():
    schema1 = {"type": "null"}
    schema2 = {"type": []}
    expected = {"null"}
    assert set(merge_types(schema1, schema2)["type"]) == expected


def test_merge_types_with_empty_arrays():
    schema1 = {"type": []}
    schema2 = {"type": []}
    assert len(set(merge_types(schema1, schema2)["type"])) == 0


def test_merge_types_with_primitive_and_non_primitive():
    schema1 = {"type": ["string"]}
    schema2 = {"type": ["object"]}
    expected = {"string"}
    assert set(merge_types(schema1, schema2)["type"]) == expected

    schema1 = {"type": ["string"]}
    schema2 = {"type": ["object"]}
    expected = {"object"}
    assert set(merge_types(schema2, schema1)["type"]) == expected


def test_merge_types_with_multiple_nulls():
    schema1 = {"type": "null"}
    schema2 = {"type": "null"}
    expected = {"null"}
    assert set(merge_types(schema1, schema2)["type"]) == expected


def test_merge_types_with_primitive_array_and_null():
    schema1 = {"type": ["null"]}
    schema2 = {"type": ["string"]}
    expected = {"string", "null"}
    assert set(merge_types(schema1, schema2)["type"]) == expected
