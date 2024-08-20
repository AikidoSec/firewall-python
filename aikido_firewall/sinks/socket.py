"""
Sink module for `socket`
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.vulnerabilities.ssrf.inspect_getaddrinfo_result import (
    inspect_getaddrinfo_result,
)

SOCKET_OPERATIONS = [
    "gethostbyname",
    "gethostbyaddr",
    "getaddrinfo",
    "create_connection",
]


def generate_aikido_function(former_func, op):
    """
    Generates a new aikido function given a former function and op
    """

    def aik_new_func(*args, **kwargs):
        res = former_func(*args, **kwargs)
        if op is "getaddrinfo":
            inspect_getaddrinfo_result(dns_results=res, hostname=args[0], port=args[1])
        logger.debug("Res %s", res)
        return res

    return aik_new_func


@importhook.on_import("socket")
def on_socket_import(socket):
    """
    Hook 'n wrap on `socket`
    Our goal is to wrap the following socket functions that take a hostname :
      -  gethostbyname() -- map a hostname to its IP number
      -  gethostbyaddr() -- map an IP number or hostname to DNS info
    https://github.com/python/cpython/blob/8f19be47b6a50059924e1d7b64277ad3cef4dac7/Lib/socket.py#L10
    Returns : Modified socket object
    """
    modified_socket = importhook.copy_module(socket)
    for op in SOCKET_OPERATIONS:
        former_func = copy.deepcopy(getattr(socket, op))
        setattr(modified_socket, op, generate_aikido_function(former_func, op))
        setattr(socket, op, generate_aikido_function(former_func, op))

    return modified_socket
