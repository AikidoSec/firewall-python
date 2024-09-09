"""Helper function file, see docstring"""

MOVED_PERMANENTLY = 301
FOUND = 302
SEE_OTHER = 303
TEMPORARY_REDIRECT = 307
PERMANENT_REDIRECT = 308

REDIRECT_CODES = [
    MOVED_PERMANENTLY,
    FOUND,
    SEE_OTHER,
    TEMPORARY_REDIRECT,
    PERMANENT_REDIRECT,
]


def is_redirect_status_code(status_code):
    """Checks if this status code is a redirect code"""
    return status_code in REDIRECT_CODES
