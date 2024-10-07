"""Exports is_same_type"""


def is_same_type(first, second):
    """Checks if the type is the same for first and second"""
    if isinstance(first, list) and isinstance(second, list):
        return do_type_arrays_match(first, second)

    if isinstance(first, list) and not isinstance(second, list):
        return do_type_arrays_match(first, [second])

    if not isinstance(first, list) and isinstance(second, list):
        return do_type_arrays_match([first], second)

    return first == second


def do_type_arrays_match(first, second):
    """Checks if both arrays are the same in terms of types"""
    if len(first) != len(second):
        return False

    return all(type in second for type in first)
