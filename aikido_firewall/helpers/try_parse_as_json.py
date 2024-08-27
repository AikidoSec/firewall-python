"""Function helper file, see docstring"""

import json


def try_parse_as_json(data):
    """Try to parse a string as JSON. Returns None if parsing fails."""
    try:
        return json.loads(data)
    except (ValueError, TypeError):
        return None
