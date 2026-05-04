"""Wraps starlette.applications for initial request_handler"""

from aikido_zen.context import Context
from aikido_zen.context.apply_or_bypass import apply_context_or_bypass
from ..functions.request_handler import request_handler
from ...helpers.get_argument import get_argument
from ...sinks import on_import, patch_function, before


@before
def _call(func, instance, args, kwargs):
    scope = get_argument(args, kwargs, 0, "scope")
    if not hasattr(scope, "get") or scope.get("type") != "http":
        return

    new_context = Context(req=scope, source="starlette")
    apply_context_or_bypass(new_context)
    request_handler(stage="init")


@on_import("starlette.applications", "starlette", version_requirement="0.16.0")
def patch(m):
    """
    patching module starlette.applications
    - patches: Starlette.__call__
    """
    patch_function(m, "Starlette.__call__", _call)
