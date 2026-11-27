"""Exports set_asgi_attributes_on_context"""

from urllib.parse import parse_qs
from aikido_zen.helpers.get_ip_from_request import get_ip_header_name, resolve_client_ip
from aikido_zen.helpers.logging import logger
from ..parse_cookies import parse_cookies
from .normalize_asgi_headers import normalize_asgi_headers
from .build_url_from_asgi import build_url_from_asgi


def set_asgi_attributes_on_context(context, scope):
    """
    This extracts ASGI Scope attributes, described in:
    https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope
    """
    logger.debug("Setting ASGI attributes")
    context.method = scope["method"]
    raw_headers = tuple(scope["headers"])
    context.headers = normalize_asgi_headers(raw_headers)

    # Parse every Cookie header in both its decoded readings, so no value is missed.
    context.cookies = parse_cookies(*context.headers.get("COOKIE", []))

    context.url = build_url_from_asgi(scope)
    context.query = parse_qs(scope["query_string"].decode("utf-8", errors="replace"))

    raw_ip = scope["client"][0] if scope["client"] else ""
    ip_header = get_asgi_client_ip_header(raw_headers)
    context.remote_address = resolve_client_ip(raw_ip, ip_header)


def get_asgi_client_ip_header(headers):
    # context.headers maps - to _, so a client's x_forwarded_for would count as well.
    name = get_ip_header_name().lower().encode("latin-1", "replace")
    # A proxy adds its own line at the end, and earlier lines can come from the client.
    for key, value in reversed(headers):
        if key.lower() == name:
            return value.decode("latin-1")
    return None
