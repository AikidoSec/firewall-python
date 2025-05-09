"""`Django` source module"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
from aikido_zen.background_process.packages import is_package_compatible, ANY_VERSION
from ..functions.request_handler import request_handler
from .run_init_stage import run_init_stage
from .pre_response_middleware import pre_response_middleware
from ...helpers.get_argument import get_argument
from ...sinks import on_import, patch_function, before, after


@before
def _get_response_before(func, instance, args, kwargs):
    request = get_argument(args, kwargs, 0, "request")

    run_init_stage(request)

    if pre_response_middleware not in instance._view_middleware:
        # The rate limiting middleware needs to be last in the chain.
        instance._view_middleware += [pre_response_middleware]


@after
def _get_response_after(func, instance, args, kwargs, return_value):
    if hasattr(return_value, "status_code"):
        request_handler(stage="post_response", status_code=return_value.status_code)


@on_import("django.core.handlers.base")
def patch(m):
    """
    Patch for _get_response
    - before: Parse body, create context & add middleware to run before a response
    # https://github.com/django/django/blob/5865ff5adcf64da03d306dc32b36e87ae6927c85/django/core/handlers/base.py#L174
    """
    patch_function(m, "BaseHandler._get_response", _get_response_before)
    patch_function(m, "BaseHandler._get_response", _get_response_after)
