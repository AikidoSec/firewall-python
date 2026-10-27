"""Exports set_asgi_attributes_on_context"""

from urllib.parse import parse_qs
from aikido_zen.helpers.get_ip_from_request import get_ip_from_request
from aikido_zen.helpers.logging import logger
from ..parse_cookies import parse_cookies
from .normalize_asgi_headers import normalize_asgi_headers
from .build_url_from_asgi import build_url_from_asgi


def set_asgi_attributes_on_context(context, scope):
    """
    This extracts ASGI Scope attributes, described in :
    https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope
    """
    logger.debug("Setting ASGI attributes")
    context.method = scope["method"]
    context.headers = normalize_asgi_headers(scope["headers"])

    # A client can send several Cookie headers, and Starlette merges them all.
    context.cookies = {}
    for cookie_header in context.headers.get("COOKIE", []):
        context.cookies.update(parse_cookies(cookie_header))

    context.url = build_url_from_asgi(scope)
    context.query = parse_qs(scope["query_string"].decode("utf-8", errors="replace"))

    raw_ip = scope["client"][0] if scope["client"] else ""
    context.remote_address = get_ip_from_request(raw_ip, context.headers)
