"""
Sink module for `socket`
"""
from aikido_zen.context import get_current_context
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, before, after
from aikido_zen.vulnerabilities import run_vulnerability_scan
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.errors import AikidoSSRF


@before
def _getaddrinfo_before(func, instance, args, kwargs):
    """Before wrapper for getaddrinfo - handles blocking"""
    host = get_argument(args, kwargs, 0, "host")

    # Check if we should block this outgoing request based on configuration
    cache = get_cache()
    if cache and cache.config:

        # Allow bypassed ips to access all hostnames
        context = get_current_context()
        if context and cache.is_bypassed_ip(context.remote_address):
            return

        if cache.config.should_block_outgoing_request(host):
            raise AikidoSSRF(
                f"Zen has blocked an outbound connection: socket.getaddrinfo to {host}"
            )

    op = "socket.getaddrinfo"
    register_call(op, "outgoing_http_op")


@after
def _getaddrinfo_after(func, instance, args, kwargs, return_value):
    """After wrapper for getaddrinfo - handles vulnerability scanning"""
    host = get_argument(args, kwargs, 0, "host")
    port = get_argument(args, kwargs, 1, "port")

    op = "socket.getaddrinfo"
    # Run vulnerability scan with the return value (DNS results)
    arguments = (return_value, host, port)
    run_vulnerability_scan(kind="ssrf", op=op, args=arguments)


@on_import("socket")
def patch(m):
    """
    patching module socket
    - patches getaddrinfo(host, port, ...)
    """
    patch_function(m, "getaddrinfo", _getaddrinfo_before)
    patch_function(m, "getaddrinfo", _getaddrinfo_after)
