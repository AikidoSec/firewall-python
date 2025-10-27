"""Exports run_init_stage function"""

import json
from aikido_zen.context import Context
from aikido_zen.helpers.logging import logger
from .extract_body import extract_body_from_django_request
from .extract_cookies import extract_cookies_from_django_request
from ..functions.request_handler import request_handler


def run_init_stage(request):
    """Parse request and body, run "init" stage with request_handler"""
    body = extract_body_from_django_request(request)
    cookies = extract_cookies_from_django_request(request)

    # In a separate try-catch we set the context :
    try:
        context = None
        if (
            hasattr(request, "scope") and request.scope is not None
        ):  # This request is an ASGI request
            context = Context(req=request.scope, body=body, source="django_async")
        elif hasattr(request, "META") and request.META is not None:  # WSGI request
            context = Context(req=request.META, body=body, source="django")
        else:
            return
        context.set_cookies(cookies)
        context.set_as_current_context()

        # Init stage needs to be run with context already set :
        request_handler(stage="init")
    except Exception as e:
        logger.debug("Exception occurred in run_init_stage function (Django): %s", e)
