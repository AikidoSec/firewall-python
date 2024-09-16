"""Exports set_wsgi_attributes_on_context"""

from urllib.parse import parse_qs
from aikido_zen.helpers.get_ip_from_request import get_ip_from_request
from aikido_zen.helpers.logging import logger
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
    if "COOKIE" in context.headers:
        context.cookies = parse_cookies(context.headers["COOKIE"])
    else:
        context.cookies = {}
    context.url = build_url_from_wsgi(environ)
    context.query = parse_qs(environ["QUERY_STRING"])
    context.remote_address = get_ip_from_request(
        environ["REMOTE_ADDR"], context.headers
    )

    # Content type is generally not included as a header, do include this as a header to simplify :
    if "CONTENT_TYPE" in environ:
        context.headers["CONTENT_TYPE"] = environ["CONTENT_TYPE"]
