"""Exports get_data_schema function"""

from .merge_data_schemas import merge_data_schemas

# Maximum depth to traverse the data structure to get the schema for improved performance
MAX_TRAVERSAL_DEPTH = 20
# Maximum amount of array members to merge into one
MAX_ARRAY_DEPTH = 10
# Maximum number of properties per level
MAX_PROPS = 100


def get_data_schema(data, depth=0):
    """
    Get the schema of the data (for example, HTTP JSON body) as a schema.
    """
    if data is None:
        # Handle None as a special case
        return {"type": "null"}

    # If the data is not an object (or an array), return the type
    if not isinstance(data, (dict, list, tuple)):
        type_normalized = normalize_python_types(type(data).__name__)
        return {"type": type_normalized}

    if isinstance(data, (list, tuple)):
        # Assume that the array is homogenous (for performance reasons)
        items = None
        for i in range(min(MAX_ARRAY_DEPTH, len(data))):
            current_data_schema = get_data_schema(data[i])
            if items is None:
                items = current_data_schema
            else:
                items = merge_data_schemas(items, current_data_schema)

        return {"type": "array", "items": items}

    schema = {"type": "object", "properties": {}}

    # If the depth is less than the maximum depth, get the schema for each property
    if depth < MAX_TRAVERSAL_DEPTH:
        prop_count = 0
        for key, value in data.items():
            if prop_count >= MAX_PROPS:
                # We cannot allow more properties than MAX_PROPS, breaking for loop.
                break
            schema["properties"][key] = get_data_schema(value, depth + 1)
            prop_count += 1

    return schema


def normalize_python_types(type_name):
    """
    Normalizes python types :
    str -> string
    int,float -> number
    bool -> boolean
    """
    if type_name == "str":
        return "string"
    if type_name in ["int", "float"]:
        return "number"
    if type_name == "bool":
        return "boolean"
    return type_name
