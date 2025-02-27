"""
Django Web Framework
Instrumentation for django.core.handlers.base.BaseHandler.get_response(...),
This invokes Django's middleware chain and returns the response. (For WSGI)
---
Django source code for get_response(...) :
https://github.com/django/django/blob/5865ff5adcf64da03d306dc32b36e87ae6927c85/django/core/handlers/base.py#L136
"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.background_process.packages import pkg_compat_check, ANY_VERSION
from ..functions.on_init_handler import on_init_handler, BlockResult
from ..functions.on_post_request_handler import on_post_request_handler
from .create_context import create_context
from ... import logger


def get_response_decorator(func):
    def wrapper(self, request):
        try:
            # Check if the request is blocked (e.g. geo restrictions, bot blocking, ...)
            block_result = on_init_handler(create_context(request))
            if block_result.blocking:
                return create_http_response(block_result)
        except Exception as e:
            logger.debug(
                "Django get_response() instrumentation, exception occurred: %s", e
            )

        # Get response and report status code for route discovery, api specs, ...
        res = func(self, request)
        if hasattr(res, "status_code"):
            on_post_request_handler(status_code=res.status_code)
        return res

    return wrapper


@importhook.on_import("django.core.handlers.base")
def django_get_response_instrumentation(django):
    if not pkg_compat_check("django", required_version=ANY_VERSION):
        return django

    modified_django = importhook.copy_module(django)

    # pylint: disable=no-member
    setattr(
        modified_django.BaseHandler,
        "get_response",
        get_response_decorator(django.BaseHandler.get_response),
    )
    return modified_django


def create_http_response(block_result: BlockResult):
    # pylint:disable=import-outside-toplevel # We don't want to install this by default
    from django.http import HttpResponse

    return HttpResponse(block_result.message, status=block_result.status_code)
