"""Helper function file"""

from .try_parse_url import try_parse_url


def path_to_string(path):
    """Converts an obj that represents a path into a string"""
    if isinstance(path, str):
        parsed_url = try_parse_url(path)
        if parsed_url:
            return parsed_url.path
        return path

    if isinstance(path, bytes):
        try:
            return path.decode("utf-8")
        except UnicodeDecodeError:
            return None
    return None
