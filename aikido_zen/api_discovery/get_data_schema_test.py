import pytest
from .get_data_schema import get_data_schema


def test_get_data_schema():
    assert get_data_schema("test") == {
        "type": "string",
    }


def test_get_data_schema_2():
    assert get_data_schema(["test"]) == {
        "type": "array",
        "items": {
            "type": "string",
        },
    }


def test_get_data_schema_3():
    assert get_data_schema({"test": "abc"}) == {
        "type": "object",
        "properties": {
            "test": {
                "type": "string",
            },
        },
    }


def test_get_data_schema_4():
    assert get_data_schema({"test": 123, "arr": [1, 2, 3]}) == {
        "type": "object",
        "properties": {
            "test": {
                "type": "number",
            },
            "arr": {
                "type": "array",
                "items": {
                    "type": "number",
                },
            },
        },
    }


def test_get_data_schema_5():
    assert get_data_schema({"test": 123, "arr": [{"sub": True}], "x": None}) == {
        "type": "object",
        "properties": {
            "test": {
                "type": "number",
            },
            "arr": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sub": {
                            "type": "boolean",
                        },
                    },
                },
            },
            "x": {
                "type": "null",
            },
        },
    }


def test_get_data_schema_6():
    assert get_data_schema(
        {
            "test": {
                "x": {
                    "y": {
                        "z": 123,
                    },
                },
            },
            "arr": [],
        }
    ) == {
        "type": "object",
        "properties": {
            "test": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "object",
                        "properties": {
                            "y": {
                                "type": "object",
                                "properties": {
                                    "z": {
                                        "type": "number",
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "arr": {
                "type": "array",
                "items": None,
            },
        },
    }


def test_get_data_schema_7():
    assert get_data_schema(
        {
            "test": 123,
            "arr": [{"sub": True}, {"sub2": True, "sub": True}, {"sub": True}],
            "x": None,
        }
    ) == {
        "type": "object",
        "properties": {
            "test": {
                "type": "number",
            },
            "arr": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sub": {
                            "type": "boolean",
                        },
                        "sub2": {"type": "boolean", "optional": True},
                    },
                },
            },
            "x": {
                "type": "null",
            },
        },
    }


def generate_test_object_with_depth(depth):
    if depth == 0:
        return "testValue"

    return {
        "prop": generate_test_object_with_depth(depth - 1),
    }


def generate_object_with_properties(count):
    obj = {}
    for i in range(count):
        obj[f"props{i}"] = i
    return obj


def test_max_depth():
    obj = generate_test_object_with_depth(10)
    schema = get_data_schema(obj)
    assert "'type': 'string'" in str(schema)

    obj2 = generate_test_object_with_depth(20)
    schema2 = get_data_schema(obj2)
    assert "'type': 'string'" in str(schema2)

    obj3 = generate_test_object_with_depth(21)
    schema3 = get_data_schema(obj3)
    assert "'type': 'string'" not in str(schema3)


def test_max_properties():
    obj = generate_object_with_properties(80)
    schema = get_data_schema(obj)
    assert len(schema["properties"]) == 80

    obj2 = generate_object_with_properties(100)
    schema2 = get_data_schema(obj2)
    assert len(schema2["properties"]) == 100

    obj3 = generate_object_with_properties(120)
    schema3 = get_data_schema(obj3)
    assert len(schema3["properties"]) == 100
