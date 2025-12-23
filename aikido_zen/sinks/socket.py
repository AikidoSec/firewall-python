"""
Sink module for `socket`
"""

from aikido_zen.context import get_current_context
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, patch_function, after
from aikido_zen.vulnerabilities import run_vulnerability_scan
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.errors import AikidoSSRF


def report_and_check_hostname(hostname, port):
    cache = get_cache()
    if not cache:
        return

    cache.hostnames.add(hostname, port)

    context = get_current_context()
    is_bypassed = context and cache.is_bypassed_ip(context.remote_address)

    if cache.config and not is_bypassed:
        if cache.config.should_block_outgoing_request(hostname):
            raise AikidoSSRF(f"Zen has blocked an outbound connection to {hostname}")


@after
def _getaddrinfo_after(func, instance, args, kwargs, return_value):
    """After wrapper for getaddrinfo - handles vulnerability scanning and hostname reporting"""
    host = get_argument(args, kwargs, 0, "host")
    port = get_argument(args, kwargs, 1, "port")

    report_and_check_hostname(host, port)

    # Run vulnerability scan with the return value (DNS results)
    op = "socket.getaddrinfo"
    arguments = (return_value, host, port)
    run_vulnerability_scan(kind="ssrf", op=op, args=arguments)


@on_import("socket")
def patch(m):
    """
    patching module socket
    - patches getaddrinfo(host, port, ...)
    """
    patch_function(m, "getaddrinfo", _getaddrinfo_after)
