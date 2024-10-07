"""Exports function merge_data_schemas"""

import copy
from .is_same_type import is_same_type
from .merge_types import merge_types


def merge_data_schemas(first, second):
    """
    Merge two data schemas into one, getting all properties from both schemas to capture
    optional properties. If the types are different, only primitive types are merged.
    Merging of arrays with objects or objects / arrays with primitive types is not supported.
    In this case the first schema is preferred over the second schema because it can already
    contain multiple merged schemas.
    """
    result = copy.deepcopy(first)

    if not is_same_type(first.get("type"), second.get("type")):
        return merge_types(first, second)

    if first.get("properties") is not None and second.get("properties") is not None:
        result["properties"] = first.get("properties")

        for key, second_schema in second.get("properties").items():
            if key in result.get("properties"):
                result["properties"][key] = merge_data_schemas(
                    result.get("properties")[key], second_schema
                )
            else:
                result["properties"][key] = second_schema

                # If a property is not in the first schema, we can assume it is optional
                # because we only store schemas for requests with status 2xx
                result["properties"][key]["optional"] = True

        for key in first.get("properties"):
            # Check if removed in second schema
            if key not in second.get("properties"):
                result["properties"][key]["optional"] = True

    if first.get("items") and second.get("items"):
        result["items"] = merge_data_schemas(first.get("items"), second.get("items"))

    return result
