"""
Exports `parse_cookies` function which parses WSGI cookies
"""

from http.cookies import SimpleCookie


def parse_cookies(cookie_str):
    """Parse cookie string from headers"""
    cookie_dict = {}
    cookies = SimpleCookie()
    cookies.load(cookie_str)

    for key, morsel in cookies.items():
        cookie_dict[key] = morsel.value

    return cookie_dict
