"""
Sink module for `socket`
"""

from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, before
from aikido_zen.vulnerabilities import run_vulnerability_scan
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.errors import AikidoSSRF


@before
def _getaddrinfo(func, instance, args, kwargs):
    host = get_argument(args, kwargs, 0, "host")
    port = get_argument(args, kwargs, 1, "port")

    # Check if we should block this outgoing request based on configuration
    cache = get_cache()
    if cache and cache.config:
        if cache.config.should_block_outgoing_request(host):
            raise AikidoSSRF(
                f"Zen has blocked an outbound connection: socket.getaddrinfo to {host}"
            )

    op = "socket.getaddrinfo"
    register_call(op, "outgoing_http_op")

    # Call the original function to get the return value for vulnerability scanning
    return_value = func(*args, **kwargs)

    # Run vulnerability scan after getting the result
    arguments = (return_value, host, port)  # return_value = dns response
    run_vulnerability_scan(kind="ssrf", op=op, args=arguments)

    return return_value


@on_import("socket")
def patch(m):
    """
    patching module socket
    - patches getaddrinfo(host, port, ...)
    """
    patch_function(m, "getaddrinfo", _getaddrinfo)
