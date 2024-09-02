"""
`Django` source module for django-gunicorn, intercepts django import and adds Aikido middleware
"""

# pylint:disable=protected-access
import json
import copy
import importhook
from aikido_firewall.context import Context
from aikido_firewall.background_process.packages import add_wrapped_package
from .functions.request_handler import request_handler


def gen_aikido_middleware_function(former__middleware_chain):
    """
    Aikido's middleware function, handles request
    """

    def aikido_middleware_function(request):
        # Get a parsed body from Django :
        body = request.POST.dict()
        if len(body) == 0 and request.content_type == "application/json":
            try:
                body = json.loads(request.body)
            except Exception:
                pass
        if len(body) == 0:
            # E.g. XML Data
            body = request.body

        context = Context(req=request.META, body=body, source="django")
        context.set_as_current_context()
        request_handler(stage="init")

        res = former__middleware_chain(request)
        request_handler(stage="post_response", status_code=res.status_code)
        return res

    return aikido_middleware_function


def aikido_ratelimiting_middleware(request, *args, **kwargs):
    """Aikido middleware that handles ratelimiting"""
    response = request_handler(stage="pre_response")
    if response:
        # pylint:disable=import-outside-toplevel # We don't want to install this by default
        from django.http import HttpResponse

        return HttpResponse(response[0], status=response[1])
    return None


@importhook.on_import("django.core.handlers.base")
def on_django_gunicorn_import(django):
    """
    Hook 'n wrap on `django.core.handlers.base`
    Our goal is to wrap the `load_middleware` function
    # https://github.com/django/django/blob/790f0f8868b0cde9a9bec1f0621efa53b00c87df/django/core/handlers/base.py#L140
    So we can wrap te `_middleware_chain` function.
    Returns : Modified django.core.handlers.base object
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
