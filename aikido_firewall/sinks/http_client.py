"""
Sink module for `http`
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger


@importhook.on_import("http.client")
def on_http_import(http):
    """
    Hook 'n wrap on `http.client.HTTPConnection.putrequest`
    Our goal is to wrap the putrequest() function of the HTTPConnection class :
    https://github.com/python/cpython/blob/372df1950817dfcf8b9bac099448934bf8657cf5/Lib/http/client.py#L1136
    Returns : Modified http.client object
    """
    modified_http = importhook.copy_module(http)
    former_putrequest = copy.deepcopy(http.HTTPConnection.putrequest)

    def aik_new_putrequest(_self, method, url, *args, **kwargs):
        logger.info("HTTP Request [%s] %s:%s %s", method, _self.host, _self.port, url)
        res = former_putrequest(_self, method, url, *args, **kwargs)
        logger.info(res)
        return res

    # pylint: disable=no-member
    setattr(http.HTTPConnection, "putrequest", aik_new_putrequest)
    logger.debug("Wrapped `http` module")
    return modified_http
