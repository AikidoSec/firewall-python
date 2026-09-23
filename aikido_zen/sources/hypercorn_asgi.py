from aikido_zen.context import get_current_context
from .functions.asgi_middleware import InternalASGIMiddleware
from ..helpers.get_argument import get_argument
from ..sinks import on_import, patch_function, before_async, after
from aikido_zen.helpers.logging import logger

@before_async
async def _call_before(func, instance, args, kwargs):
    scope = get_argument(args, kwargs, 0, "scope")
    receive = get_argument(args, kwargs, 1, "receive")
    send = get_argument(args, kwargs, 2, "send")
    await InternalASGIMiddleware(instance.app, "hypercorn_asgi")(scope, receive, send)


@on_import("hypercorn.app_wrappers", "hypercorn")
def patch(m):
    """
    https://github.com/pgjones/hypercorn/blob/0e2311f1ad2ae587aaa590f3824f59aa5dc0e770/src/hypercorn/asyncio/__init__.py#L13
    We patch serve(...), which gets the ASGI app.
    And we want to be the first middleware to run.
    - patches Quart.__call__ (handles internal asgi middleware)
    - patches Quart.handle_request (Stores body/cookies)
    """
    patch_function(m, "ASGIWrapper.__call__", _call_before)
