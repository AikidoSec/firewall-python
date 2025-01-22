"""Exports merge_types function"""

from .is_primitive_type import only_contains_primitive_types


def merge_types(first, second):
    """Merge types into one schema if they are different."""

    # Currently we do not support merging arrays and other objects and
    # arrays/objects with primitive types
    first_primitive = only_contains_primitive_types(first["type"])
    second_primitive = only_contains_primitive_types(second["type"])
    if not first_primitive or not second_primitive:
        if first["type"] == "null":  # Prefer non-null type
            return second
        return first
    first["type"] = merge_type_arrays(first["type"], second["type"])
    return first


def merge_type_arrays(first, second):
    """Merge two lists of types into one"""
    if not isinstance(first, list):
        first = [first]

    if not isinstance(second, list):
        second = [second]
    return list(set(first).union(set(second)))  # Merging and removing duplicates
