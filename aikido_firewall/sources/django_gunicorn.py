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



@importhook.on_import("django.views.generic.base")
def on_flask_import(django):
    """
    Hook 'n wrap on `django.views.generic.base`
    Our goal is to wrap the `dispatch` function of the generic View class
    # https://github.com/django/django/blob/790f0f8868b0cde9a9bec1f0621efa53b00c87df/django/views/generic/base.py#L133
    so we can insert our middleware. Returns : Modified flask.app object
    """
    modified_django = importhook.copy_module(django)

    former_dispatch = copy.deepcopy(django.View.dispatch)

    def aikido_new_dispatch(_self, request, *args, **kwargs):
        raise Exception("Hewow")
        logger.critical("Request object django : %s", request)
        logger.critical("Request object dict django : %s", request.__dict__)

        return former_dispatch(_self, request, *args, **kwargs)

    # pylint: disable=no-member
    setattr(modified_django.View, "dispatch", aikido_new_dispatch)
    setattr(django.View, "dispatch", aikido_new_dispatch)

    add_wrapped_package("django")
    return modified_django
