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


def wrap_view_func(former_view_func):
    """Adds aikido wrapping to view_func function"""

    def wrapped_view_func(*args, **kwargs):
        logger.debug(args)
        logger.debug(kwargs)
        raise Exception("Yooohooo")
        return former_view_func(*args, **kwargs)

    return wrapped_view_func


def wrap__decorator(_decorator):
    """Adds aikido wrapping to _decorator function"""
    logger.debug("Wrapping _decorator object")
    former__decorator = copy.deepcopy(_decorator)

    def aikido__decorator(*args, **kwargs):
        return wrap_view_func(former__decorator(*args, **kwargs))

    return aikido__decorator


def wrap__make_decorator(_make_decorator):
    """Adds aikido wrapping to _make_decorator function"""
    former__make_decorator = copy.deepcopy(_make_decorator)

    def aikido__make_decorator(*args, **kwargs):
        return wrap__decorator(former__make_decorator(*args, **kwargs))

    return aikido__make_decorator


@importhook.on_import("django.utils.decorators")
def on_flask_import(django):
    """
    Hook 'n wrap on `django.views.generic.base`
    Our goal is to wrap the `view_func` function
    `make_middleare_decorator` function |> `_make_decorator` function |> `_decorator` function |> `view_func`
    # https://github.com/django/django/blob/790f0f8868b0cde9a9bec1f0621efa53b00c87df/django/utils/decorators.py#L194
    Returns : Modified django.utils.decorators object
    """
    modified_django = importhook.copy_module(django)

    former_aikido_make_middleware_decorator = copy.deepcopy(
        django.make_middleware_decorator
    )

    def aikido_make_middleware_decorator(*args):
        response = former_aikido_make_middleware_decorator(*args)
        return wrap__make_decorator(response)

    # pylint: disable=no-member
    setattr(
        modified_django, "make_middleware_decorator", aikido_make_middleware_decorator
    )
    setattr(django, "make_middleware_decorator", aikido_make_middleware_decorator)

    add_wrapped_package("django")
    return modified_django
