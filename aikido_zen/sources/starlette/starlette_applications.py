"""Wraps starlette.applications for initial request_handler"""

from aikido_zen.context import Context
from ..functions.request_handler import request_handler
from ...helpers.get_argument import get_argument
from ...sinks import on_import, patch_function, before_async


@before_async
async def _call(func, instance, args, kwargs):
    scope = get_argument(args, kwargs, 1, "scope")
    if scope.get("type") != "http":
        return

    new_context = Context(req=scope, source="starlette")
    new_context.set_as_current_context()
    request_handler(stage="init")


@on_import("starlette.applications", "starlette")
def on_starlette_import(starlette):
    """
    patches `starlette.applications`
    - patching Starlette.__call__
    """
    patch_function("Starlette", "__call__", _call)
