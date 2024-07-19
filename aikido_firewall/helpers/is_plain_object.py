"""
Helper function file, see funtion definition
"""


def is_plain_object(o):
    """
    Checks if the object is a plain object,
    i.e. a dictionary in Python
    """
    return str(type(o)) == "<class 'dict'>"
