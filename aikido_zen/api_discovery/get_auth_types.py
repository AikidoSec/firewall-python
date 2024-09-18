"""Usefull export : get_auth_types"""

from aikido_zen.helpers.is_http_auth_scheme import is_http_auth_scheme

common_api_key_header_names = [
    "x-api-key",
    "api-key",
    "apikey",
    "x-token",
    "token",
]

# Common auth cookie names
common_auth_cookie_names = [
    "auth",
    "session",
    "jwt",
    "token",
    "sid",
    "connect.sid",
    "auth_token",
    "access_token",
    "refresh_token",
] + common_api_key_header_names


def get_auth_types(context):
    """Get the authentication type of the API request."""
    if not isinstance(context.headers, dict):
        return None

    result = []

    # Check the Authorization header
    auth_header = context.headers.get("AUTHORIZATION")
    if isinstance(auth_header, str):
        auth_header_type = get_authorization_header_type(auth_header)
        if auth_header_type:
            result.append(auth_header_type)

    # Check for type apiKey in headers and cookies
    result.extend(find_api_keys(context))

    return result if result else None


def get_authorization_header_type(auth_header):
    """Get the authentication type from the Authorization header."""
    if not auth_header:
        return None
    if " " in auth_header:
        type_, value = auth_header.split(" ", 1)

        if isinstance(type_, str) and isinstance(value, str):
            if is_http_auth_scheme(type_):
                return {"type": "http", "scheme": type_.lower()}

    # Default to apiKey if the auth type is not recognized
    return {"type": "apiKey", "in": "header", "name": "Authorization"}


def find_api_keys(context):
    """Search for API keys in headers and cookies."""
    result = []

    for header in common_api_key_header_names:
        if normalize_header_key(header) in context.headers:
            result.append({"type": "apiKey", "in": "header", "name": header})

    if isinstance(context.cookies, dict):
        relevant_cookies = [
            cookie
            for cookie in context.cookies
            if cookie.lower() in common_auth_cookie_names
        ]
        for cookie in relevant_cookies:
            result.append({"type": "apiKey", "in": "cookie", "name": cookie})

    return result


def normalize_header_key(header_key):
    """Normalizes the header keys"""
    return header_key.replace("-", "_").upper()
