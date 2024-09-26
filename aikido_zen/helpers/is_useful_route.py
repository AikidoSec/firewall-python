"""
Main export is the is_useful_route function
"""

import os

EXCLUDED_METHODS = ["OPTIONS", "HEAD"]
IGNORE_EXTENSIONS = ["properties", "php", "asp", "aspx", "jsp", "config"]
IGNORE_STRINGS = ["cgi-bin"]


def is_useful_route(status_code, route, method):
    """
    Checks if the route is actually useful,
    - Isn't OPTIONS or HEAD
    - Status code isn't an error or redirect code
    - Isn't a dot file e.g. .well-known
    - etc.
    """
    status_code = int(status_code)

    is_valid_code = status_code >= 200 and status_code < 400
    if not is_valid_code:
        # Status code needs to be between 200 and 400 in order for it to be "useful"
        return False

    if method in EXCLUDED_METHODS:
        return False

    segments = route.split("/")

    if any(is_dot_file(segment) for segment in segments):
        return False

    if any(contains_ignored_string(segment) for segment in segments):
        return False

    return all(is_allowed_extension(segment) for segment in segments)


def is_allowed_extension(segment):
    """Checks if the extension on the file is allowed"""
    extension = os.path.splitext(segment)[1]

    if extension and extension.startswith("."):
        extension = extension[1:]  # Remove the dot from the extension

        if 2 <= len(extension) <= 5:
            return False

        if extension in IGNORE_EXTENSIONS:
            return False

    return True


def is_dot_file(segment):
    """Checks if the current segment is a dot file"""
    if segment == ".well-known":
        return False

    return segment.startswith(".") and len(segment) > 1


def contains_ignored_string(segment):
    """Checks if the current segment contains ignored strings"""
    return any(ignored_str in segment for ignored_str in IGNORE_STRINGS)
