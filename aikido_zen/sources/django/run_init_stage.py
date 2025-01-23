"""Exports run_init_stage function"""

import json
from aikido_zen.context import Context
from aikido_zen.helpers.logging import logger
from ..functions.request_handler import request_handler


def run_init_stage(request):
    """Parse request and body, run "init" stage with request_handler"""
    body = None
    try:
        # try-catch loading of form parameters, this is to fix issue with DATA_UPLOAD_MAX_NUMBER_FIELDS :
        try:
            body = request.POST.dict()
            if len(body) == 0:
                body = None  # Reset
        except Exception:
            pass

        # Check for JSON or XML :
        if body is None and request.content_type == "application/json":
            try:
                body = json.loads(request.body)
            except Exception:
                pass
        if body is None or len(body) == 0:
            # E.g. XML Data
            body = request.body
        if body is None or len(body) == 0:
            # During a GET request, django leaves the body as an empty byte string (e.g. `b''`).
            # When an attack is detected, this body needs to be serialized which would fail.
            # So a byte string gets converted into a string to stop that from happening.
            body = ""  # Set body to an empty string.
    except Exception as e:
        logger.debug("Error occured in run_init_stage function (Django) : %s", e)

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
        context.set_as_current_context()

        # Init stage needs to be run with context already set :
        request_handler(stage="init")
    except Exception as e:
        logger.debug("Error occurred in run_init_stage function (Django): %s", e)
