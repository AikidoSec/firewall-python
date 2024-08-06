"""
Main export is the is_useful_route function
"""

import os

NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
MOVED_PERMANENTLY = 301
FOUND = 302
SEE_OTHER = 303
TEMPORARY_REDIRECT = 307
PERMANENT_REDIRECT = 308
ERROR_CODES = [NOT_FOUND, METHOD_NOT_ALLOWED]
REDIRECT_CODES = [
    MOVED_PERMANENTLY,
    FOUND,
    SEE_OTHER,
    TEMPORARY_REDIRECT,
    PERMANENT_REDIRECT,
]
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
    if method in EXCLUDED_METHODS:
        return False

    if status_code in ERROR_CODES:
        return False

    if status_code in REDIRECT_CODES:
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
