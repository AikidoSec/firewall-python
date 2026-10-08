"""Wraps starlette.applications for initial request_handler"""

from aikido_zen.context import Context
from ..functions.request_handler import request_handler
from ...helpers.get_argument import get_argument
from ...sinks import on_import, patch_function, before
from ...helpers.logging import logger


@before
def _call(func, instance, args, kwargs):
    scope = get_argument(args, kwargs, 0, "scope")
    if not hasattr(scope, "get") or scope.get("type") != "http":
        return

    new_context = Context(req=scope, source="starlette")
    new_context.set_as_current_context()
    request_handler(stage="init")

    # Perform firewall enforcement at the application entry point to ensure
    # mounted ASGI applications and custom ASGI callables are also protected
    try:
        pre_response_results = request_handler(stage="pre_response")
        if pre_response_results:
            response = create_starlette_response(pre_response_results)
            if response:
                # Block the request by returning the firewall response
                return response
        # Mark firewall as enforced to avoid duplicate checks in routing wrapper
        new_context.firewall_enforced = True
        new_context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred in pre_response stage at __call__: %s", e)


def create_starlette_response(pre_response):
    """Tries to import PlainTextResponse and generates starlette plain text response"""
    text, status_code = pre_response
    try:
        from starlette.responses import PlainTextResponse
    except ImportError:
        logger.info(
            "Ensure `starlette` install is valid, failed to import starlette.responses"
        )
        return None
    return PlainTextResponse(text, status_code)


@on_import("starlette.applications", "starlette", version_requirement="0.16.0")
def patch(m):
    """
    patching module starlette.applications
    - patches: Starlette.__call__
    """
    patch_function(m, "Starlette.__call__", _call)
