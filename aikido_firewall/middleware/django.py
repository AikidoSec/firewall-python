"""
Django WSGI Aikido Middleware
uses headers, body, etc. as sources
"""

from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.is_useful_route import is_useful_route
from aikido_firewall.context import Context
from aikido_firewall.errors import AikidoRateLimiting


class AikidoMiddleware:
    """
    Same as docstring above
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        logger.debug("Aikido middleware for `django` was called : __call__")
        context = Context(req=request, source="django")
        context.set_as_current_context()

        response = self.get_response(request)
        comms = get_comms()

        is_curr_route_useful = is_useful_route(
            response.status_code, context.route, context.method
        )
        if is_curr_route_useful:
            comms.send_data_to_bg_process("ROUTE", (context.method, context.route))
        # comms.send_data_to_bg_process("STATS:ADD_REQ", ())

        ratelimit = comms.send_data_to_bg_process("SHOULD_RATELIMIT", context, True)
        if ratelimit and ratelimit.get("block"):
            raise AikidoRateLimiting()

        return response

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
