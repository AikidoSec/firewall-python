"""Helper function file, see function docstring"""

import json


def serialize_to_json(obj):
    """
    Tries to serialize the object, if that fails
    it tries to convert the object to a dict and then serialize
    if that fails it returns an empty JSON string "{}"
    """
    try:
        return json.dumps(obj)
    except Exception:
        try:
            return json.dumps(dict(obj))
        except Exception:
            pass
    return "{}"
