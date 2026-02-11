"""Helper function file"""

from urllib3.util import parse_url
from pathlib import PurePath


def path_to_string(path):
    """Converts an obj that represents a path into a string"""
    if isinstance(path, str):
        try:
            parsed_url = parse_url(path)
            if parsed_url and parsed_url.scheme == "file":
                return parsed_url.path
        except Exception:
            print("can't parse thsi shit! bye")
            return None
        return path
    print("can't parse thsi shit! bye - 9")

    if isinstance(path, bytes):
        try:
            return path.decode("utf-8")
        except UnicodeDecodeError:
            print("can't parse thsi shit! by - 4 e")
            return None
    if isinstance(path, PurePath):
        # Stringify PurePath. This can still allow path traversal but in extremely
        # limited cases so it's safe to just stringify for now.
        return str(path)
    

    print("can't parse thsi shit! bye - 1")
    return None
