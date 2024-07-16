"""
Django WSGI Aikido Middleware
uses headers, body, etc. as sources
"""

import logging


class AikidoMiddleware:
    """
    Same as docstring above
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        logging.critical("[AIK] Aikido middleware : call")
        return self.get_response(request)

    def process_exception(self, request, exception):
        """
        Do something when an exception occurs whilst django is processing a request
        """
        logging.critical("[AIK] Aikido middleware : exception")

    def process_request(self, request):
        """
        Not entirely sure, but should be executed when django receives requests
        """
        logging.critical("[AIK] Aikido middleware : request")
