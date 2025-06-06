"""
Sink module for `http`
"""

from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import before, after, patch_function, on_import
from aikido_zen.vulnerabilities.ssrf.handle_http_response import (
    handle_http_response,
)
from aikido_zen.helpers.try_parse_url import try_parse_url


@before
def _putrequest(func, instance, args, kwargs):
    # putrequest(...) is called with path argument, store this on the HTTPConnection
    # instance for later use in the getresponse(...) function.
    path = get_argument(args, kwargs, 1, "path")
    setattr(instance, "_aikido_var_path", path)


@after
def _getresponse(func, instance, args, kwargs, return_value):
    path = getattr(instance, "_aikido_var_path")
    source_url = try_parse_url(f"http://{instance.host}:{instance.port}{path}")

    register_call("HTTPConnection.getresponse", "outgoing_http_op")

    handle_http_response(http_response=return_value, source=source_url)


@on_import("http.client")
def patch(m):
    """
    patching module http.client
    - patches HTTPConnection.putrequest -> stores path
    - patches HTTPConnection.getresponse -> handles response object
    """
    patch_function(m, "HTTPConnection.putrequest", _putrequest)
    patch_function(m, "HTTPConnection.getresponse", _getresponse)
