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
from ..functions.check_if_request_is_blocked import (
    check_if_request_is_blocked,
    BlockResult,
)
from ..functions.request_handler import request_handler
from .create_context import create_context
from ... import logger


@importhook.on_import("django.core.handlers.base")
def django_get_response_instrumentation(django):
    if not pkg_compat_check("django", required_version=ANY_VERSION):
        return django

    modified_django = importhook.copy_module(django)
    get_response_original = copy.deepcopy(django.BaseHandler.get_response)

    def get_response_modified(self, request):
        try:
            # Extract context for Django :
            context = create_context(request)
            context.set_as_current_context()
            request_handler(stage="init")

            # Check if the request is blocked (e.g. geo restrictions, bot blocking, ...)
            block_result = check_if_request_is_blocked(context)
            if block_result.blocking:
                return create_http_response(block_result)
        except Exception as e:
            logger.debug(
                "Django get_response() instrumentation, exception occurred: %s", e
            )

        # Get response and report status code for route discovery, api specs, ...
        res = get_response_original(self, request)
        if hasattr(res, "status_code"):
            request_handler(stage="post_response", status_code=res.status_code)
        return res

    # pylint: disable=no-member
    setattr(modified_django.BaseHandler, "get_response", get_response_modified)
    setattr(django.BaseHandler, "get_response", get_response_modified)

    return modified_django


def create_http_response(block_result: BlockResult):
    # pylint:disable=import-outside-toplevel # We don't want to install this by default
    from django.http import HttpResponse

    return HttpResponse(block_result.message, status=block_result.status_code)
