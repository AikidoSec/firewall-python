"""
Sink module for `http`
"""

from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import after, patch_function, on_import
from aikido_zen.vulnerabilities.ssrf.handle_http_response import (
    handle_http_response,
)
from aikido_zen.helpers.try_parse_url import try_parse_url


@after
def _getresponse(func, instance, args, kwargs, return_value):
    path = get_argument(args, kwargs, 1, "path")
    source_url = try_parse_url(f"http://{instance.host}:{instance.port}{path}")
    handle_http_response(http_response=return_value, source=source_url)


@on_import("http.client")
def patch(m):
    """
    patching module http.client
    - patches HTTPConnection.getresponse
    """
    patch_function(m, "HTTPConnection.getresponse", _getresponse)
