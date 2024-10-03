"""
Helper function file, see funtion definition
"""

from collections.abc import Mapping


def is_mapping(o):
    """
    Checks if the object is a plain object,
    i.e. an instance of Mapping in Python
    """
    return isinstance(o, Mapping)
