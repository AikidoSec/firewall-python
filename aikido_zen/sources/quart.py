from aikido_zen.context import Context, get_current_context
from .functions.request_handler import request_handler
from ..helpers.get_argument import get_argument
from ..sinks import on_import, patch_function, before, before_async


@before
def _call(func, instance, args, kwargs):
    scope = get_argument(args, kwargs, 0, "scope")
    if not scope or scope.get("type") != "http":
        return

    new_context = Context(req=scope, source="quart")
    new_context.set_as_current_context()
    request_handler(stage="init")


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


async def _handle_request_after(func, instance, args, kwargs):
    # pylint:disable=import-outside-toplevel # We don't want to install this by default
    from werkzeug.exceptions import HTTPException

    try:
        response = await func(*args, **kwargs)
        if hasattr(response, "status_code"):
            request_handler(stage="post_response", status_code=response.status_code)
        return response
    except HTTPException as e:
        request_handler(stage="post_response", status_code=e.code)
        raise e


async def _asgi_app(func, instance, args, kwargs):
    scope = get_argument(args, kwargs, 0, "scope")
    if not scope or scope.get("type") != "http":
        return await func(*args, **kwargs)
    send = get_argument(args, kwargs, 2, "send")
    if not send:
        return await func(*args, **kwargs)

    pre_response = request_handler(stage="pre_response")
    if pre_response:
        return await send_status_code_and_text(send, pre_response)
    return await func(*args, **kwargs)


async def send_status_code_and_text(send, pre_response):
    await send(
        {
            "type": "http.response.start",
            "status": pre_response[1],
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": pre_response[0].encode("utf-8"),
            "more_body": False,
        }
    )


@on_import("quart.app", "quart")
def patch(m):
    """
    patching module quart.app
    - patches Quart.__call__ (creates Context)
    - patches Quart.handle_request (Stores body/cookies, checks status code)
    - patches Quart.asgi_app (Pre-response: puts in messages when request is blocked)
    """
    patch_function(m, "Quart.__call__", _call)
    patch_function(m, "Quart.handle_request", _handle_request_before)
    patch_function(m, "Quart.handle_request", _handle_request_after)
    patch_function(m, "Quart.asgi_app", _asgi_app)
