"""
Django WSGI Aikido Middleware
uses headers, body, etc. as sources
"""

from aikido_firewall.helpers.logging import logger


class AikidoMiddleware:
    """
    Same as docstring above
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        logger.debug("Aikido middleware for `django` was called : __call__")
        return self.get_response(request)

    def process_exception(self, request, exception):
        """
        Do something when an exception occurs whilst django is processing a request
        """
        logger.debug("Aikido middleware for `django` was called : process_exception")

    def process_request(self, request):
        """
        executed during the request phase of the Django request-response cycle.
        """
        logger.debug("Aikido middleware for `django` was called : process_request")
