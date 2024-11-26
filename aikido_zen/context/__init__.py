"""
Provides all the functionality for contexts
"""

import contextvars
import json
from json import JSONDecodeError
from time import sleep
from urllib.parse import parse_qs

from aikido_zen.helpers.build_route_from_url import build_route_from_url
from aikido_zen.helpers.get_subdomains_from_url import get_subdomains_from_url
from aikido_zen.helpers.logging import logger
from .wsgi import set_wsgi_attributes_on_context
from .asgi import set_asgi_attributes_on_context
from .extract_route_params import extract_route_params

UINPUT_SOURCES = ["body", "cookies", "query", "headers", "xml", "route_params"]
current_context = contextvars.ContextVar("current_context", default=None)

WSGI_SOURCES = ["django", "flask"]
ASGI_SOURCES = ["quart", "django_async", "starlette"]


def get_current_context():
    """Returns the current context"""
    try:
        return current_context.get()
    except Exception:
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
        self.set_body(body)

        # Parse WSGI/ASGI/... request :
        self.cookies = self.method = self.remote_address = self.query = self.headers = (
            self.url
        ) = None
        if source in WSGI_SOURCES:
            set_wsgi_attributes_on_context(self, req)
        elif source in ASGI_SOURCES:
            set_asgi_attributes_on_context(self, req)

        # Define variables using parsed request :
        self.route = build_route_from_url(self.url)
        self.route_params = extract_route_params(self.url)
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
                    "route_params": self.route_params,
                },
                None,
                None,
            ),
        )

    def set_as_current_context(self):
        """
        Set the current context
        """
        current_context.set(self)

    def set_body(self, body):
        """Sets the body and checks if it's possibly JSON"""
        self.body = body
        if isinstance(body, bytes) and len(body) == 0:
            # Make sure that empty bodies like b"" don't get sent.
            self.body = None
        if isinstance(self.body, str) and self.body.startswith("{"):
            # Might be JSON, but might not have been parsed correctly by server because of wrong headers
            try:
                # Check if body is JSON :
                parsed_body = json.loads(self.body)
                if parsed_body:
                    self.body = parsed_body
            except JSONDecodeError:
                pass

    def get_route_metadata(self):
        """Returns a route_metadata object"""
        return {
            "method": self.method,
            "route": self.route,
            "url": self.url,
        }
