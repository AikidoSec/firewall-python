"""Exports run_init_stage function"""

from aikido_zen.context import Context
from .try_extract_body import try_extract_body_from_django_request
from .try_extract_cookies import try_extract_cookies_from_django_request
from ..functions.request_handler import request_handler


def run_init_stage(request):
    """Parse request and body, run "init" stage with request_handler"""
    context = None
    if (
        hasattr(request, "scope") and request.scope is not None
    ):  # This request is an ASGI request
        context = Context(req=request.scope, source="django_async")
    elif hasattr(request, "META") and request.META is not None:  # WSGI request
        context = Context(req=request.META, source="django")
    else:
        return

    # Parse some attributes separately
    context.body = try_extract_body_from_django_request(request)
    context.cookies = try_extract_cookies_from_django_request(request)

    context.set_as_current_context()
    request_handler(stage="init")
