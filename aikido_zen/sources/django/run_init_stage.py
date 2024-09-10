"""Exports run_init_stage function"""

import json
from aikido_zen.context import Context
from aikido_zen.helpers.logging import logger
from ..functions.request_handler import request_handler


def run_init_stage(request):
    """Parse request and body, run "init" stage with request_handler"""
    try:
        request_handler(stage="init")
        body = request.POST.dict()
        if len(body) == 0 and request.content_type == "application/json":
            try:
                body = json.loads(request.body)
            except Exception:
                pass
        if len(body) == 0:
            # E.g. XML Data
            body = request.body

        context = None
        if hasattr(request, "scope"):  # This request is an ASGI request
            context = Context(req=request.scope, body=body, source="django_async")
        elif hasattr(request, "META"):  # WSGI request
            context = Context(req=request.META, body=body, source="django")
        context.set_as_current_context()
    except Exception as e:
        logger.debug("Error occured in run_init_stage function (Django) : %s", e)
