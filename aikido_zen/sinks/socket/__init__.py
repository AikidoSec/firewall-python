"""
Sink module for `socket`
"""

from aikido_zen.errors import AikidoSSRF
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, patch_function, after
from aikido_zen.sinks.socket.normalize_hostname import normalize_hostname
from aikido_zen.sinks.socket.should_block_outbound_domain import (
    should_block_outbound_domain,
)
from aikido_zen.vulnerabilities import run_vulnerability_scan


@after
def _getaddrinfo_after(func, instance, args, kwargs, return_value):
    """After wrapper for getaddrinfo - handles vulnerability scanning and hostname reporting"""
    host = get_argument(args, kwargs, 0, "host")
    port = get_argument(args, kwargs, 1, "port")

    # We want a normalized hostname for reporting & blocking outbound domains
    # This function decodes the hostname if its written in punycode
    hostname = normalize_hostname(host)

    # Store hostname and check if we should stop this request from happening
    if should_block_outbound_domain(hostname, port):
        raise AikidoSSRF(f"Zen has blocked an outbound connection to {hostname}")

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
