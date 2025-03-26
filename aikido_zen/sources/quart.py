"""
Quart source module, intercepts quart import and adds Aikido middleware
"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
from aikido_zen.context import Context, get_current_context
from aikido_zen.background_process.packages import is_package_compatible, ANY_VERSION
from .functions.request_handler import request_handler


async def aikido___call___wrapper(former_call, quart_app, scope, receive, send):
    """Aikido's __call__ wrapper"""
    # We don't want to install werkzeug :
    # pylint: disable=import-outside-toplevel
    try:
        if scope["type"] != "http":
            return await former_call(quart_app, scope, receive, send)
        context1 = Context(req=scope, source="quart")
        context1.set_as_current_context()

        request_handler(stage="init")
    except Exception as e:
        logger.debug("Exception on aikido __call__ function : %s", e)
    return await former_call(quart_app, scope, receive, send)


async def handle_request_wrapper(former_handle_request, quart_app, req):
    """
    https://github.com/pallets/quart/blob/2fc6d4fa6e3df017e8eef1411ec80b5a6dce25a5/src/quart/app.py#L1400
    Wraps the handle_request function
    """
    # At this stage no middleware is called yet, running pre_response is
    # not what we need to do now, but we can store the body inside context :
    try:
        context = get_current_context()
        if context:
            form = await req.form
            if req.is_json:
                context.set_body(await req.get_json())
            elif form:
                context.set_body(form)
            else:
                data = await req.data
                context.set_body(data.decode("utf-8"))
            context.cookies = req.cookies.to_dict()
            context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception in handle_request : %s", e)

    # Fetch response and run post_response handler :
    # pylint:disable=import-outside-toplevel # We don't want to install this by default
    from werkzeug.exceptions import HTTPException

    try:
        response = await former_handle_request(quart_app, req)
        status_code = response.status_code
        request_handler(stage="post_response", status_code=status_code)
        return response
    except HTTPException as e:
        request_handler(stage="post_response", status_code=e.code)
        raise e


async def send_status_code_and_text(send, pre_response):
    """Sends a status code and text"""
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


@importhook.on_import("quart.app")
def on_quart_import(quart):
    """
    Hook 'n wrap on `quart.app`
    Our goal is to wrap the __call__, handle_request, asgi_app functios of the "Quart" class
    """
    if not is_package_compatible("quart", required_version=ANY_VERSION):
        return quart
    modified_quart = importhook.copy_module(quart)

    former_handle_request = copy.deepcopy(quart.Quart.handle_request)
    former_asgi_app = copy.deepcopy(quart.Quart.asgi_app)
    former_call = copy.deepcopy(quart.Quart.__call__)

    async def aikido___call__(quart_app, scope, receive=None, send=None):
        return await aikido___call___wrapper(
            former_call, quart_app, scope, receive, send
        )

    async def aikido_handle_request(quart_app, request):
        return await handle_request_wrapper(former_handle_request, quart_app, request)

    async def aikido_asgi_app(quart_app, scope, receive=None, send=None):
        if scope["type"] == "http":
            # Run pre_response code :
            pre_response = request_handler(stage="pre_response")
            if pre_response:
                return await send_status_code_and_text(send, pre_response)
        return await former_asgi_app(quart_app, scope, receive, send)

    # pylint:disable=no-member # Pylint has issues with the wrapping
    setattr(modified_quart.Quart, "__call__", aikido___call__)
    setattr(modified_quart.Quart, "handle_request", aikido_handle_request)
    setattr(modified_quart.Quart, "asgi_app", aikido_asgi_app)
    return modified_quart
