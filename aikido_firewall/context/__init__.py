"""
Provides all the functionality for contexts
"""

import threading
from urllib.parse import parse_qs

from aikido_firewall.helpers.build_route_from_url import build_route_from_url
from aikido_firewall.helpers.get_subdomains_from_url import get_subdomains_from_url
from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.get_ip_from_request import get_ip_from_request
from .parse_cookies import parse_cookies

SUPPORTED_SOURCES = ["django", "flask"]
UINPUT_SOURCES = ["body", "cookies", "query", "headers"]

local = threading.local()


def get_current_context():
    """Returns the current context"""
    try:
        return local.current_context
    except AttributeError:
        return None


def extract_wsgi_headers(request):
    headers = {}
    for key, value in request.items():
        if key.startswith("HTTP_"):
            # Remove the 'HTTP_' prefix and store in the headers dictionary
            headers[key[5:]] = value
    return headers


def build_url_from_wsgi(request):
    scheme = request["wsgi.url_scheme"]
    host = request["HTTP_HOST"]
    uri = request["PATH_INFO"]
    return f"{scheme}://{host}{uri}"


def parse_body_string(body_string):
    return body_string


class Context:
    """
    A context object, it stores everything that is important
    for vulnerability detection
    """

    def __init__(self, context_obj=None, req=None, raw_body=None, source=None):
        if context_obj:
            logger.info("Context object setting")
            self.__dict__.update(context_obj)
            return

        if not source in SUPPORTED_SOURCES:
            raise ValueError(f"Source {source} not supported")
        self.source = source
        logger.debug("Setting wsgi attributes")
        self.method = req["REQUEST_METHOD"]
        self.headers = extract_wsgi_headers(req)
        if "COOKIE" in self.headers:
            self.cookies = parse_cookies(self.headers["COOKIE"])
        else:
            self.cookies = {}
        self.url = build_url_from_wsgi(req)
        self.query = parse_qs(req["QUERY_STRING"])
        self.body = raw_body
        self.route = build_route_from_url(self.url)
        self.subdomains = get_subdomains_from_url(self.url)
        self.user = None
        self.remote_address = get_ip_from_request(req["REMOTE_ADDR"], self.headers)

    def __reduce__(self):
        return (
            self.__class__,
            (
                {
                    "method": self.method,
                    "remote_address": self.remote_address,
                    "url": self.url,
                    "body": self.body,
                    "headers": self.headers,
                    "query": self.query,
                    "cookies": self.cookies,
                    "source": self.source,
                    "route": self.route,
                    "subdomains": self.subdomains,
                    "user": self.user,
                },
                None,
                None,
            ),
        )

    def set_as_current_context(self):
        """
        Set the current context
        """
        local.current_context = self
