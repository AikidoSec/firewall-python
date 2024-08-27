"""
Sink module for `http`
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.vulnerabilities import run_vulnerability_scan


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
        logger.debug("HTTP Request [%s] %s:%s %s", method, _self.host, _self.port, url)
        url_object = {"href": url, "hostname": _self.host}
        run_vulnerability_scan(
            kind="ssrf", op="http.client.putrequest", args=(url_object, _self.port)
        )
        return former_putrequest(_self, method, url, *args, **kwargs)

    # pylint: disable=no-member
    setattr(http.HTTPConnection, "putrequest", aik_new_putrequest)
    return modified_http
