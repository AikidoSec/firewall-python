"""
`Django` source module for django-gunicorn, intercepts django import and adds Aikido middleware
"""

import json
import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import Context, get_current_context
from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.is_useful_route import is_useful_route
from aikido_firewall.background_process.packages import add_wrapped_package


def gen_aikido_middleware_function(former__middleware_chain):
    """
    Aikido's middleware function, handles request
    """

    def aikido_middleware_function(request):
        get_comms().send_data_to_bg_process("STATISTICS", {"action": "request"})
        context = Context(
            req=request.META, raw_body=request.body.decode("utf-8"), source="django"
        )
        logger.info("Context : %s", json.dumps(context.__dict__))
        context.set_as_current_context()

        res = former__middleware_chain(request)
        is_curr_route_useful = is_useful_route(
            res.status_code,
            context.route,
            context.method,  #  Pretend the status code is 200
        )
        if is_curr_route_useful:
            get_comms().send_data_to_bg_process(
                "ROUTE", (context.method, context.route)
            )
        return res

    return aikido_middleware_function


def aikido_ratelimiting_middleware(request, *args, **kwargs):
    """Aikido middleware that handles ratelimiting"""
    context = get_current_context()
    if not context:
        return
    # Blocked users:
    if context.user:
        blocked_res = get_comms().send_data_to_bg_process(
            action="SHOULD_BLOCK_USER", obj=context.user["id"], receive=True
        )
        if blocked_res["success"] and blocked_res["data"]:
            # We don't want to install django, import on demand
            from django.http import HttpResponse

            return HttpResponse("You are blocked by Aikido Firewall.", status=403)

    # Ratelimiting :
    ratelimit_res = get_comms().send_data_to_bg_process(
        action="SHOULD_RATELIMIT", obj=context, receive=True
    )
    if ratelimit_res["success"] and ratelimit_res["data"]["block"]:
        # We don't want to install django, import on demand
        from django.http import HttpResponse

        message = "You are rate limited by Aikido firewall"
        if ratelimit_res["data"]["trigger"] is "ip":
            message += f" (Your IP: {context.remote_address})"
        return HttpResponse(message, status=429)


@importhook.on_import("django.core.handlers.base")
def on_django_gunicorn_import(django):
    """
    Hook 'n wrap on `django.core.handlers.base`
    Our goal is to wrap the `load_middleware` function
    # https://github.com/django/django/blob/790f0f8868b0cde9a9bec1f0621efa53b00c87df/django/core/handlers/base.py#L140
    So we can wrap te `_middleware_chain` function; Returns : Modified django.core.handlers.base object
    """
    modified_django = importhook.copy_module(django)

    former_load_middleware = copy.deepcopy(django.BaseHandler.load_middleware)

    def aikido_load_middleware(_self, *args, **kwargs):
        response = former_load_middleware(_self, *args, **kwargs)
        #  We are the first middleware to be called :
        former__middleware_chain = copy.deepcopy(_self._middleware_chain)
        _self._middleware_chain = gen_aikido_middleware_function(
            former__middleware_chain
        )

        # The rate limiting middleware needs to be added as the last middleware in the chain :
        _self._view_middleware = _self._view_middleware + [
            aikido_ratelimiting_middleware
        ]
        return response

    # pylint: disable=no-member
    setattr(modified_django.BaseHandler, "load_middleware", aikido_load_middleware)
    setattr(django.BaseHandler, "load_middleware", aikido_load_middleware)

    add_wrapped_package("django")
    return modified_django
