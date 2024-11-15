"""
Sink module for `http`
"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
from aikido_zen.vulnerabilities import run_vulnerability_scan
from aikido_zen.vulnerabilities.ssrf.handle_http_response import (
    handle_http_response,
)
from aikido_zen.helpers.try_parse_url import try_parse_url
from aikido_zen.errors import AikidoException


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
    former_getresponse = copy.deepcopy(http.HTTPConnection.getresponse)

    def aik_new_putrequest(_self, method, path, *args, **kwargs):
        #  Aikido putrequest, gets called before the request goes through
        # Set path for aik_new_getresponse :
        _self.aikido_attr_path = path
        return former_putrequest(_self, method, path, *args, **kwargs)

    def aik_new_getresponse(_self):
        #  Aikido getresponse, gets called after the request is complete
        # And fetches the response
        response = former_getresponse(_self)
        try:
            assembled_url = f"http://{_self.host}:{_self.port}{_self.aikido_attr_path}"
            source_url = try_parse_url(assembled_url)
            handle_http_response(http_response=response, source=source_url)
        except Exception as e:
            logger.debug("Exception occured in custom getresponse function : %s", e)
        return response

    # pylint: disable=no-member
    setattr(http.HTTPConnection, "putrequest", aik_new_putrequest)
    # pylint: disable=no-member
    setattr(http.HTTPConnection, "getresponse", aik_new_getresponse)
    return modified_http
