from .is_primitive_type import only_contains_primitive_types, is_primitive_type


def test_only_contains_primitive_types_single_primitive():
    assert only_contains_primitive_types("string") is True
    assert only_contains_primitive_types("number") is True
    assert only_contains_primitive_types("boolean") is True


def test_only_contains_primitive_types_single_non_primitive():
    assert only_contains_primitive_types("object") is False
    assert only_contains_primitive_types("array") is False


def test_only_contains_primitive_types_multiple_primitives():
    assert only_contains_primitive_types(["string", "number", "boolean"]) is True


def test_only_contains_primitive_types_mixed():
    assert only_contains_primitive_types(["string", "object", "number"]) is False
    assert only_contains_primitive_types(["array", "boolean"]) is False


def test_only_contains_primitive_types_empty():
    assert only_contains_primitive_types([]) is True  # An empty list should return True


def test_only_contains_primitive_types_non_list_input():
    assert only_contains_primitive_types("string") is True
    assert only_contains_primitive_types("object") is False
