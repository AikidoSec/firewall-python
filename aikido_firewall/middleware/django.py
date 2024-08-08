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
        comms = get_comms()

        # Ratelimiting code :
        ratelimit_res = comms.send_data_to_bg_process(
            action="SHOULD_RATELIMIT", obj=context, receive=True
        )
        if ratelimit_res["success"] and ratelimit_res["data"]["block"]:
            from django.http import (
                HttpResponse,
            )  #  We don't want to install django, import on demand

            message = "You are rate limited by Aikido firewall"
            if ratelimit_res["data"]["trigger"] is "ip":
                message += f" (Your IP: {context.remote_address})"
            return HttpResponse(message, status=429)

        response = self.get_response(request)

        # Reporting route code :
        is_curr_route_useful = is_useful_route(
            response.status_code, context.route, context.method
        )
        if is_curr_route_useful:
            comms.send_data_to_bg_process("ROUTE", (context.method, context.route))

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
