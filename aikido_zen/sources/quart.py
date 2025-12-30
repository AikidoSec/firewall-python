import inspect
from aikido_zen.context import get_current_context
from .functions.asgi_middleware import InternalASGIMiddleware
from ..helpers.get_argument import get_argument
from ..sinks import on_import, patch_function, before_async, after


async def _call_coroutine(func, instance, args, kwargs):
    scope = get_argument(args, kwargs, 0, "scope")
    receive = get_argument(args, kwargs, 1, "receive")
    send = get_argument(args, kwargs, 2, "send")

    await InternalASGIMiddleware(func, "quart")(scope, receive, send)


@after
def _call(func, instance, args, kwargs, return_value):
    """
    Legacy ASGI v2.0
    func: application(scope)
    return_value: coroutine application_instance(receive, send)
    """
    scope = get_argument(args, kwargs, 0, "scope")

    async def application_instance(receive, send):
        await InternalASGIMiddleware(return_value, "quart")(scope, receive, send)

    # Modify return_value
    return_value = application_instance


@before_async
async def _handle_request_before(func, instance, args, kwargs):
    context = get_current_context()
    if not context:
        return

    request = get_argument(args, kwargs, 0, "request")
    if not request:
        return

    form = await request.form
    if request.is_json:
        context.set_body(await request.get_json())
    elif form:
        context.set_body(form)
    else:
        data = await request.data
        context.set_body(data.decode("utf-8"))
    context.cookies = request.cookies.to_dict()
    context.set_as_current_context()


@on_import("quart.app", "quart")
def patch(m):
    """
    We patch Quart.__call__ instead of asgi_app, because asgi_app itself can be wrapped multiple times
    And we want to be the first middleware to run.
    - patches Quart.__call__ (handles internal asgi middleware)
    - patches Quart.handle_request (Stores body/cookies)
    """

    if inspect.iscoroutine(m.Quart.__call__):
        # coroutine application(scope, receive, send)
        patch_function(m, "Quart.__call__", _call_coroutine)
    else:
        # Legacy ASGI v2.0
        # https://asgi.readthedocs.io/en/latest/specs/main.html#legacy-applications
        # application(scope): coroutine application_instance(receive, send)
        patch_function(m, "Quart.__call__", _call)

    patch_function(m, "Quart.handle_request", _handle_request_before)
