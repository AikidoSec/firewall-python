"""Helper function file"""

from urllib.parse import urlparse


def path_to_string(path):
    """Converts an obj that represents a path into a string"""
    if isinstance(path, str):
        try:
            parsed_url = urlparse(path)
            if parsed_url and parsed_url.scheme == "file":
                return parsed_url.path
        except Exception:
            return None
        return path

    if isinstance(path, bytes):
        try:
            return path.decode("utf-8")
        except UnicodeDecodeError:
            return None
    return None
