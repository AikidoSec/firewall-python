import pytest
from .merge_data_schemas import merge_data_schemas


@pytest.fixture
def schema_a():
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
    }


@pytest.fixture
def schema_b():
    return {
        "type": "object",
        "properties": {
            "age": {"type": "integer"},
            "email": {"type": "string"},
        },
    }


@pytest.fixture
def schema_c():
    return {"type": "null"}


@pytest.fixture
def schema_d():
    return {
        "type": "object",
        "properties": {
            "address": {"type": "string"},
        },
    }


@pytest.fixture
def schema_e():
    return {
        "type": "array",
        "items": {"type": "string"},
    }


@pytest.fixture
def schema_f():
    return {"type": "array", "items": {"type": "integer"}}


def test_merge_same_type_schemas(schema_a, schema_b):
    merged = merge_data_schemas(schema_a, schema_b)
    props = merged.get("properties")
    assert props["name"].get("type") == "string"
    assert props["age"].get("type") == "integer"
    assert props["email"].get("type") == "string"
    assert props["age"].get("optional") is None
    assert props["email"].get("optional") is True


def test_merge_different_type_schemas(schema_a, schema_c):
    merged = merge_data_schemas(schema_a, schema_c)
    assert merged == schema_a


def test_merge_null_type_preference(schema_c, schema_b):
    merged = merge_data_schemas(schema_c, schema_b)
    assert merged == schema_b


def test_merge_with_optional_properties(schema_a, schema_d):
    merged = merge_data_schemas(schema_a, schema_d)
    assert "address" in merged["properties"]
    assert merged["properties"]["address"]["optional"] is True


def test_merge_array_schemas(schema_e, schema_f):
    merged = merge_data_schemas(schema_e, schema_f)
    assert merged["type"] == "array"
    assert (
        merged["items"]["type"] == "string"
    )  # Assuming we prefer the first schema's item type


def test_merge_empty_properties(schema_a):
    empty_schema = {"type": "object", "properties": {}}
    merged = merge_data_schemas(schema_a, empty_schema)
    assert merged["properties"] == schema_a["properties"]


def test_merge_with_no_properties(schema_a):
    no_properties_schema = {"type": "object", "properties": {}}
    merged = merge_data_schemas(no_properties_schema, schema_a)
    assert merged["properties"] == schema_a["properties"]


def test_merge_with_nested_schemas(schema_a, schema_b):
    nested_schema_a = {"type": "object", "properties": {"details": schema_a}}
    nested_schema_b = {"type": "object", "properties": {"details": schema_b}}
    merged = merge_data_schemas(nested_schema_a, nested_schema_b)
    assert "details" in merged["properties"]
    assert merged["properties"]["details"]["properties"]["name"]["type"] == "string"
    assert merged["properties"]["details"]["properties"]["email"]["type"] == "string"
    assert merged["properties"]["details"]["properties"]["age"]["type"] is "integer"


def test_merge_with_no_items(schema_e):
    empty_array_schema = {"type": "array", "items": None}
    merged = merge_data_schemas(schema_e, empty_array_schema)
    assert merged["items"] == schema_e["items"]


def test_merge_with_different_item_types(schema_e, schema_f):
    merged = merge_data_schemas(schema_e, schema_f)
    assert merged["items"].get("type") == "string"
