"""Exports set_wsgi_attributes_on_context"""

from urllib.parse import parse_qs
from aikido_zen.helpers.get_ip_from_request import (
    get_ip_from_request,
    get_ip_header_name,
    is_ip,
    normalize_ip,
)
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.trust_proxy import (
    CIDRTrustProxy,
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
    raw_ip = environ["REMOTE_ADDR"]
    # Werkzeug's ProxyFix keeps the connection address here. A different REMOTE_ADDR is
    # the client ProxyFix chose, which Zen uses instead of parsing the header again.
    connection_ip = (
        environ.get("werkzeug.proxy_fix.orig", {}).get("REMOTE_ADDR") or raw_ip
    )
    context.is_behind_trusted_proxy = is_trusted_proxy_request(connection_ip)
    if connection_ip != raw_ip and get_ip_header_name() == "X_FORWARDED_FOR":
        client_ip = normalize_ip(raw_ip)
        cidr_mode = isinstance(get_trust_proxy_config(), CIDRTrustProxy)
        unlisted_connection = cidr_mode and not context.is_behind_trusted_proxy
        # The same fallbacks as without ProxyFix.
        if unlisted_connection or not is_ip(client_ip):
            client_ip = connection_ip
        context.remote_address = client_ip if is_ip(client_ip) else None
    else:
        context.remote_address = get_ip_from_request(connection_ip, context.headers)

    # Content type is generally not included as a header, do include this as a header to simplify :
    if "CONTENT_TYPE" in environ:
        context.headers.store_header("CONTENT_TYPE", environ["CONTENT_TYPE"])
