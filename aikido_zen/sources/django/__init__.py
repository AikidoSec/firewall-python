"""`Django` source module"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
from aikido_zen.background_process.packages import pkg_compat_check, ANY_VERSION
from ..functions.request_handler import request_handler
from .run_init_stage import run_init_stage
from .pre_response_middleware import pre_response_middleware


@importhook.on_import("django.core.handlers.base")
def on_django_gunicorn_import(django):
    """
    Hook 'n wrap on `django.core.handlers.base`
    Our goal is to wrap the `_get_response` function
    # https://github.com/django/django/blob/5865ff5adcf64da03d306dc32b36e87ae6927c85/django/core/handlers/base.py#L174
    Returns : Modified django.core.handlers.base object
    """
    if not pkg_compat_check("django", required_version=ANY_VERSION):
        return django
    modified_django = importhook.copy_module(django)

    former__get_response = copy.deepcopy(django.BaseHandler._get_response)

    def aikido__get_response(self, request):  # Synchronous (WSGI)
        run_init_stage(request)  # We do some initial request handling

        if pre_response_middleware not in self._view_middleware:
            # The rate limiting middleware needs to be last in the chain.
            self._view_middleware += [pre_response_middleware]

        res = former__get_response(self, request)
        if hasattr(res, "status_code"):
            request_handler(stage="post_response", status_code=res.status_code)
        return res

    # pylint: disable=no-member
    setattr(modified_django.BaseHandler, "_get_response", aikido__get_response)
    setattr(django.BaseHandler, "_get_response", aikido__get_response)

    return modified_django
