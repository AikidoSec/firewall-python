"""
Provides all the functionality for contexts
"""

import threading
from urllib.parse import parse_qs

from .wsgi import set_wsgi_attributes_on_context
from aikido_firewall.helpers.build_route_from_url import build_route_from_url
from aikido_firewall.helpers.get_subdomains_from_url import get_subdomains_from_url
from aikido_firewall.helpers.logging import logger

UINPUT_SOURCES = ["body", "cookies", "query", "headers", "xml"]
local = threading.local()


def get_current_context():
    """Returns the current context"""
    try:
        return local.current_context
    except AttributeError:
        return None


class Context:
    """
    A context object, it stores everything that is important
    for vulnerability detection
    """

    def __init__(self, context_obj=None, body=None, req=None, source=None):
        if context_obj:
            logger.debug("Creating Context instance based on dict object.")
            self.__dict__.update(context_obj)
            return
        # Define emtpy variables/Properties :
        self.source = source
        self.user = None
        self.parsed_userinput = {}
        self.xml = {}
        self.outgoing_req_redirects = []
        self.body = body

        # Parse WSGI/ASGI/... request :
        self.cookies = self.method = self.remote_address = self.query = self.headers = (
            self.url
        ) = None
        set_wsgi_attributes_on_context(self, req)

        # Define variables using parsed request :
        self.route = build_route_from_url(self.url)
        self.subdomains = get_subdomains_from_url(self.url)

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
                    "xml": self.xml,
                    "outgoing_req_redirects": self.outgoing_req_redirects,
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

    def get_route_metadata(self):
        """Returns a route_metadata object"""
        return {
            "method": self.method,
            "route": self.route,
            "url": self.url,
        }
