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
from aikido_firewall.context.wsgi_request_to_context import wsgi_request_to_context


def aikido_middleware_function(request, *args, **kwargs):
    """
    Aikido's middleware function, handles request
    """
    logger.debug(request)
    logger.debug(request.__dict__)
    logger.debug(request.GET)
    wsgi_request_to_context(request)
    raise Exception("Gotcha")

@importhook.on_import("django.core.handlers.base")
def on_django_gunicorn_import(django):
    """
    Hook 'n wrap on `django.views.generic.base`
    Our goal is to wrap the `view_func` function
    `make_middleare_decorator` function |> `_make_decorator` function |> `_decorator` function |> `view_func`
    # https://github.com/django/django/blob/790f0f8868b0cde9a9bec1f0621efa53b00c87df/django/utils/decorators.py#L194
    Returns : Modified django.utils.decorators object
    """
    modified_django = importhook.copy_module(django)

    former_load_middleware = copy.deepcopy(
        django.BaseHandler.load_middleware
    )

    def aikido_load_middleware(_self, *args, **kwargs):
        response = former_load_middleware(_self, *args, **kwargs)
        logger.debug("MAKE VIEW ATOMIC RES : %s", response)
        _self._view_middleware = [aikido_middleware_function] + _self._view_middleware
        return response

    # pylint: disable=no-member
    setattr(
        modified_django.BaseHandler, "load_middleware", aikido_load_middleware
    )
    setattr(django.BaseHandler, "load_middleware", aikido_load_middleware)

    #add_wrapped_package("django")
    return modified_django
