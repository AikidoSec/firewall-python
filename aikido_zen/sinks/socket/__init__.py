"""
Sink module for `socket`
"""

from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, patch_function, after
from aikido_zen.sinks.socket.report_and_check_hostname import report_and_check_hostname
from aikido_zen.vulnerabilities import run_vulnerability_scan


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
