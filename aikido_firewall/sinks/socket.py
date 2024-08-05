"""
Sink module for `socket`
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger


def generate_aikido_function(former_func, op):
    """
    Generates a new aikido function given a former function and op
    """

    def aik_new_func(*args, **kwargs):
        logger.info("DNS LOOKUP")
        logger.debug(args)
        logger.debug(kwargs)
        return former_func(*args, **kwargs)

    return aik_new_func


@importhook.on_import("socket")
def on_socket_import(socket):
    """
    Hook 'n wrap on `socket`
    Our goal is to wrap the following socket functions that take a hostname :
      -  gethostbyname() -- map a hostname to its IP number
      -  gethostbyaddr() -- map an IP number or hostname to DNS info
    https://github.com/python/cpython/blob/8f19be47b6a50059924e1d7b64277ad3cef4dac7/Lib/socket.py#L10
    Returns : Modified http.client object
    """
    modified_socket = importhook.copy_module(socket)
    former_gethostbyname = copy.deepcopy(socket.gethostbyname)
    former_gethostbyaddr = copy.deepcopy(socket.gethostbyaddr)

    setattr(
        modified_socket,
        "gethostbyname",
        generate_aikido_function(
            former_func=former_gethostbyname, op="socket.gethostbyname"
        ),
    )
    setattr(
        modified_socket,
        "gethostbyaddr",
        generate_aikido_function(
            former_func=former_gethostbyaddr, op="socket.gethostbyaddr"
        ),
    )
    logger.debug("Wrapped `http` module")
    return modified_socket
