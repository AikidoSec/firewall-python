"""Exports is_primitive_type and only_contains_primitive_types"""


def only_contains_primitive_types(types):
    """Checks lists for primitive types or the type itself"""
    if not isinstance(types, list):
        return is_primitive_type(types)
    return all(is_primitive_type(t) for t in types)


def is_primitive_type(type_to_check):
    """Checks if the type is not an object or array"""
    return type_to_check not in ["object", "array"]
