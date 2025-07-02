from dataclasses import dataclass, field
import contextvars
import json
from typing import Any, Dict, List, Optional, Union
from aikido_zen.helpers.build_route_from_url import build_route_from_url
from aikido_zen.helpers.get_subdomains_from_url import get_subdomains_from_url
from aikido_zen.helpers.logging import logger
from .wsgi import set_wsgi_attributes_on_context
from .asgi import set_asgi_attributes_on_context
from .extract_route_params import extract_route_params

UINPUT_SOURCES = ["body", "cookies", "query", "headers", "xml", "route_params"]
current_context = contextvars.ContextVar("current_context", default=None)

def get_current_context():
    """Returns the current context"""
    try:
        return current_context.get()
    except Exception:
        return None


@dataclass
class AikidoContext:
    method: str
    url: str
    remote_address: str
    source: Optional[str] = None
    user: Optional[Any] = None
    executed_middleware: bool = False

    body: Optional[Any] = None
    cookies: Dict[str, List[str]] = field(default_factory=dict)
    query: Dict[str, List[str]] = field(default_factory=dict)
    headers: Dict[str, List[str]] = field(default_factory=dict)
    xml: Dict[str, Any] = field(default_factory=dict)

    parsed_userinput: Dict[str, Any] = field(default_factory=dict)
    outgoing_req_redirects: List[Any] = field(default_factory=list)

    route: Optional[str] = None
    route_params: Dict[str, Any] = field(default_factory=dict)
    subdomains: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.route = build_route_from_url(self.url)
        self.route_params = extract_route_params(self.url)
        self.subdomains = get_subdomains_from_url(self.url)

    def get_header(self, key: str) -> Optional[str]:
        if key not in self.headers or not self.headers[key]:
            return None
        return self.headers[key][-1]

    def set_as_current_context(self):
        current_context.set(self)

    def set_body(self, body: Optional[Any]):
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
        return self.get_header("USER_AGENT")
