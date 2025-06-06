"""
Sink module for `socket`
"""

from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, after
from aikido_zen.vulnerabilities import run_vulnerability_scan


@after
def _getaddrinfo(func, instance, args, kwargs, return_value):
    host = get_argument(args, kwargs, 0, "host")
    port = get_argument(args, kwargs, 1, "port")

    op = "socket.getaddrinfo"
    register_call(op, "outgoing_http_op")

    arguments = (return_value, host, port)  # return_value = dns response
    run_vulnerability_scan(kind="ssrf", op=op, args=arguments)


@on_import("socket")
def patch(m):
    """
    patching module socket
    - patches getaddrinfo(host, port, ...)
    """
    patch_function(m, "getaddrinfo", _getaddrinfo)
