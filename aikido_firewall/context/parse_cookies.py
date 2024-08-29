"""
Exports `parse_cookies` function which parses WSGI cookies
"""

from http.cookies import SimpleCookie, CookieError


def parse_cookies(cookie_str):
    """Parse cookie string from headers"""
    cookie_dict = {}
    cookies = SimpleCookie()
    try:
        cookies.load(cookie_str)
    except CookieError:
        # Invalid keys can cause errors, we want to ignore them
        pass

    for key, morsel in cookies.items():
        cookie_dict[key] = morsel.value

    return cookie_dict
