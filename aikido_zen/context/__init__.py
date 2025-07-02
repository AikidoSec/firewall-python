"""
Provides all the functionality for contexts
"""

import contextvars
import json
from typing import Optional, Dict, List

from aikido_zen.helpers.build_route_from_url import build_route_from_url
from aikido_zen.helpers.get_subdomains_from_url import get_subdomains_from_url
from aikido_zen.helpers.logging import logger
from .wsgi import parse_wsgi_environ, WSGIContext
from .asgi import parse_asgi_scope, ASGIContext
from .extract_route_params import extract_route_params
from ..helpers.headers import Headers

UINPUT_SOURCES = ["body", "cookies", "query", "headers", "xml", "route_params"]
current_context = contextvars.ContextVar[Optional["Context"]](
    "current_context", default=None
)

WSGI_SOURCES = ["django", "flask"]
ASGI_SOURCES = ["quart", "django_async", "starlette"]


def get_current_context() -> Optional["Context"]:
    try:
        return current_context.get()
    except LookupError:
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

        self.source = source
        self.user = None
        self.method = None
        self.remote_address = None
        self.url = None
        self.parsed_userinput = {}
        self.xml = {}
        self.outgoing_req_redirects = []
        self.headers: Headers = Headers()
        self.query: Dict[str, List[str]] = dict()
        self.cookies: Dict[str, List[str]] = dict()
        self.executed_middleware = False
        self.set_body(body)

        if source in WSGI_SOURCES:
            wsgi_context: WSGIContext = parse_wsgi_environ(req)
            self.method = wsgi_context.method
            self.remote_address = wsgi_context.remote_address
            self.url = wsgi_context.url
            self.headers = wsgi_context.headers
            self.query = wsgi_context.query
            self.cookies = wsgi_context.cookies
        elif source in ASGI_SOURCES:
            asgi_context: ASGIContext = parse_asgi_scope(req)
            self.method = asgi_context.method
            self.remote_address = asgi_context.remote_address
            self.url = asgi_context.url
            self.headers = asgi_context.headers
            self.query = asgi_context.query
            self.cookies = asgi_context.cookies
        else:
            raise Exception("Unsupported source: " + source)

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
                    "executed_middleware": self.executed_middleware,
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
        try:
            self.set_body_internal(body)
        except Exception as e:
            logger.debug("Exception occurred whilst setting body: %s", e)

    def set_body_internal(self, body):
        """Sets the body and checks if it's possibly JSON"""
        self.body = body
        if isinstance(self.body, (str, bytes)) and len(body) == 0:
            # Make sure that empty bodies like b"" don't get sent.
            self.body = None
        if isinstance(self.body, bytes):
            self.body = self.body.decode("utf-8")  # Decode byte input to string.
        if not isinstance(self.body, str):
            return
        if self.body.strip()[0] in ["{", "[", '"']:
            # Might be JSON, but might not have been parsed correctly by server because of wrong headers
            parsed_body = json.loads(self.body)
            if parsed_body:
                self.body = parsed_body

    def get_route_metadata(self):
        """Returns a route_metadata object"""
        return {
            "method": self.method,
            "route": self.route,
            "url": self.url,
        }

    def get_user_agent(self) -> Optional[str]:
        return self.headers.get_header("USER_AGENT")
