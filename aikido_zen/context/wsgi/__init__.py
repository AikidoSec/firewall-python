"""Exports set_wsgi_attributes_on_context"""

from urllib.parse import parse_qs
from aikido_zen.helpers.get_ip_from_request import get_ip_from_request
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.trust_proxy import (
    BooleanTrustProxy,
    get_trust_proxy_config,
    is_trusted_proxy_request,
)
from .extract_wsgi_headers import extract_wsgi_headers
from .build_url_from_wsgi import build_url_from_wsgi
from ..parse_cookies import parse_cookies


def set_wsgi_attributes_on_context(context, environ):
    """
    This extracts WSGI attributes, described in :
    https://peps.python.org/pep-3333/#environ-variables
    """
    logger.debug("Setting wsgi attributes")

    context.method = environ["REQUEST_METHOD"]
    context.headers = extract_wsgi_headers(environ)
    if context.headers.get_header("COOKIE"):
        context.cookies = parse_cookies(context.headers.get_header("COOKIE"))
    else:
        context.cookies = {}
    context.url = build_url_from_wsgi(environ)
    context.query = parse_qs(environ["QUERY_STRING"])
    remote_addr = environ["REMOTE_ADDR"]
    # A ProxyFix around the app keeps the connection address here.
    connection_ip = (
        environ.get("werkzeug.proxy_fix.orig", {}).get("REMOTE_ADDR") or remote_addr
    )
    context.is_behind_trusted_proxy = is_trusted_proxy_request(connection_ip)
    # Only an untrusted request can have proxy trust off, so read the setting only then.
    trust_off = not context.is_behind_trusted_proxy and (
        get_trust_proxy_config() == BooleanTrustProxy(False)
    )
    context.remote_address = get_ip_from_request(
        remote_addr if trust_off else connection_ip, context.headers
    )

    # Content type is generally not included as a header, do include this as a header to simplify :
    if "CONTENT_TYPE" in environ:
        context.headers.store_header("CONTENT_TYPE", environ["CONTENT_TYPE"])
