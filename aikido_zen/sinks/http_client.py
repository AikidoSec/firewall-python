"""
Sink module for `http`
"""

import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
from aikido_zen.vulnerabilities.ssrf.handle_http_response import (
    handle_http_response,
)
from aikido_zen.helpers.try_parse_url import try_parse_url


@importhook.on_import("http.client")
def on_http_import(http):
    """
    Hook 'n wrap on `http.client.HTTPConnection.putrequest`
    Our goal is to wrap the putrequest() function of the HTTPConnection class :
    https://github.com/python/cpython/blob/372df1950817dfcf8b9bac099448934bf8657cf5/Lib/http/client.py#L1136
    Returns : Modified http.client object
    """
    modified_http = importhook.copy_module(http)

    class AikidoHTTPConnection(http.HTTPConnection):
        def putrequest(self, method, url, skip_host=False, skip_accept_encoding=False):
            #  Aikido putrequest, gets called before the request goes through
            # Set path for aik_new_getresponse :
            self.aikido_attr_path = url
            return http.HTTPConnection.putrequest(
                self, method, url, skip_host, skip_accept_encoding
            )

        def getresponse(self):
            #  Aikido getresponse, gets called after the request is complete
            # And fetches the response
            response = http.HTTPConnection.getresponse(self)
            try:
                assembled_url = f"http://{self.host}:{self.port}{self.aikido_attr_path}"
                source_url = try_parse_url(assembled_url)
                handle_http_response(http_response=response, source=source_url)
            except Exception as e:
                logger.debug("Exception occured in custom getresponse function : %s", e)
            return response

    setattr(modified_http, "HTTPConnection", AikidoHTTPConnection)
    return modified_http
