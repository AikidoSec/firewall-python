"""
Exports `parse_cookies` function which parses WSGI cookies
"""

from http.cookies import _unquote


def parse_cookies(cookie_str):
    """Parse cookie string from headers"""
    # Unlike SimpleCookie, which stops at a value with a space, a comma or JSON,
    # this keeps every cookie, so none is hidden from the scan.
    cookie_dict = {}
    for chunk in cookie_str.split(";"):
        if "=" in chunk:
            key, val = chunk.split("=", 1)
        else:
            key, val = "", chunk
        key, val = key.strip(), val.strip()
        if key or val:
            cookie_dict[key] = _unquote(val)
    return cookie_dict
