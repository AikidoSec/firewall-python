"""
`Django` source module for django-gunicorn, intercepts django import and adds Aikido middleware
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import Context
from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.is_useful_route import is_useful_route
from aikido_firewall.errors import AikidoRateLimiting
from aikido_firewall.background_process.packages import add_wrapped_package


def aikido_middleware_function(request, *args, **kwargs):
    """
    Aikido's middleware function, handles request
    """
    context = Context(req=request, source="django")
    context.set_as_current_context()

    ratelimit_res = get_comms().send_data_to_bg_process(
        action="SHOULD_RATELIMIT", obj=context, receive=True
    )
    if ratelimit_res["success"] and ratelimit_res["data"]["block"]:
        raise AikidoRateLimiting()
    is_curr_route_useful = is_useful_route(
        200, context.route, context.method  #  Pretend the status code is 200
    )
    if is_curr_route_useful:
        get_comms().send_data_to_bg_process("ROUTE", (context.method, context.route))


@importhook.on_import("django.core.handlers.base")
def on_django_gunicorn_import(django):
    """
    Hook 'n wrap on `django.core.handlers.base`
    Our goal is to wrap the `load_middleware` function
    # https://github.com/django/django/blob/790f0f8868b0cde9a9bec1f0621efa53b00c87df/django/core/handlers/base.py#L32
    So we can add our aikido_middleware_function; Returns : Modified django.core.handlers.base object
    """
    modified_django = importhook.copy_module(django)

    former_load_middleware = copy.deepcopy(django.BaseHandler.load_middleware)

    def aikido_load_middleware(_self, *args, **kwargs):
        response = former_load_middleware(_self, *args, **kwargs)
        #  We are the first middleware to be called :
        _self._view_middleware = [aikido_middleware_function] + _self._view_middleware
        return response

    # pylint: disable=no-member
    setattr(modified_django.BaseHandler, "load_middleware", aikido_load_middleware)
    setattr(django.BaseHandler, "load_middleware", aikido_load_middleware)

    add_wrapped_package("gunicorn")
    add_wrapped_package("django")
    return modified_django
