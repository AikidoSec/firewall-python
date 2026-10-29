"""
Exports `parse_cookies` function which parses request cookies
"""

from http.cookies import _unquote


def parse_cookies(*cookie_strs):
    """Parse cookie strings from headers"""
    # Unlike SimpleCookie, this keeps every cookie, even one with a space, a comma or JSON,
    # and every value of a repeated name, because the app may read any of them.
    cookies = {}
    for cookie_str in cookie_strs:
        for chunk in cookie_str.split(";"):
            if "=" in chunk:
                key, val = chunk.split("=", 1)
            else:
                key, val = "", chunk
            key, val = key.strip(), _unquote(val.strip())
            if not key and not val:
                continue
            if key not in cookies:
                cookies[key] = val
            elif isinstance(cookies[key], list):
                if val not in cookies[key]:
                    cookies[key].append(val)
            elif cookies[key] != val:
                cookies[key] = [cookies[key], val]
    return cookies
