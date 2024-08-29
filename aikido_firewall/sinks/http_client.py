"""
Sink module for `http`
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.vulnerabilities import run_vulnerability_scan
from aikido_firewall.vulnerabilities.ssrf.handle_http_response import (
    handle_http_response,
)
from aikido_firewall.helpers.try_parse_url import try_parse_url
from aikido_firewall.errors import AikidoException


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
        #  Aikido putrequest, gets called before the request went through
        try:
            # Set path for aik_new_getresponse :
            _self.aikido_attr_path = path

            # Create a URL Object :
            assembled_url = f"http://{_self.host}:{_self.port}{path}"
            url_object = try_parse_url(assembled_url)

            run_vulnerability_scan(
                kind="ssrf", op="http.client.putrequest", args=(url_object, _self.port)
            )
        except AikidoException as e:
            raise e
        except Exception as e:
            logger.debug("Exception occured in custom putrequest function : %s", e)
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
