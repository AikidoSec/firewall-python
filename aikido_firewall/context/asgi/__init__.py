"""Exports set_wsgi_attributes_on_context"""

from urllib.parse import parse_qs
from aikido_firewall.helpers.get_ip_from_request import get_ip_from_request
from aikido_firewall.helpers.logging import logger
from ..parse_cookies import parse_cookies
from .normalize_asgi_headers import normalize_asgi_headers
from .build_url_from_asgi import build_url_from_asgi


def set_asgi_attributes_on_context(context, scope):
    """
    This extracts WSGI attributes, described in :
    https://peps.python.org/pep-3333/#environ-variables
    """
    logger.debug("Setting ASGI attributes")
    context.method = scope["method"]
    context.headers = normalize_asgi_headers(scope["headers"])

    if "COOKIE" in context.headers:
        context.cookies = parse_cookies(context.headers["COOKIE"])
    else:
        context.cookies = {}

    context.url = build_url_from_asgi(scope)
    context.query = parse_qs(scope["query_string"].decode("utf-8"))

    raw_ip = scope["client"][0] if scope["client"] else ""
    context.remote_address = get_ip_from_request(raw_ip, context.headers)