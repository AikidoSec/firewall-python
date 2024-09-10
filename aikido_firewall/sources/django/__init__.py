"""`Django` source module"""

import copy
import aikido_firewall.importhook as importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.packages import add_wrapped_package
from ..functions.request_handler import request_handler
from .run_init_stage import run_init_stage
from .ratelimiting_middleware import ratelimiting_middleware


@importhook.on_import("django.core.handlers.base")
def on_django_gunicorn_import(django):
    """
    Hook 'n wrap on `django.core.handlers.base`
    Our goal is to wrap the `_get_response` function
    # https://github.com/django/django/blob/5865ff5adcf64da03d306dc32b36e87ae6927c85/django/core/handlers/base.py#L174
    So we can change the _view_middleware function before anything else
    Returns : Modified django.core.handlers.base object
    """
    modified_django = importhook.copy_module(django)

    former__get_response = copy.deepcopy(django.BaseHandler._get_response)

    # Synchronous :
    def aikido__get_response(self, request):
        logger.debug("_get_response django function being called")
        #  We do some initial request handling :
        run_init_stage(request)

        # The rate limiting middleware needs to be added as the last middleware in the chain :
        if ratelimiting_middleware not in self._view_middleware:
            self._view_middleware += [ratelimiting_middleware]
        res = former__get_response(self, request)
        if hasattr(res, "status_code"):
            request_handler(stage="post_response", status_code=res.status_code)
        return res

    # pylint: disable=no-member
    setattr(modified_django.BaseHandler, "_get_response", aikido__get_response)
    setattr(django.BaseHandler, "_get_response", aikido__get_response)

    add_wrapped_package("django")
    return modified_django
