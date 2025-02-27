"""
Quart source module, intercepts quart import and adds Aikido middleware
"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
from aikido_zen.context import Context, get_current_context
from aikido_zen.background_process.packages import pkg_compat_check, ANY_VERSION
from .asgi import asgi_decorator
from .functions.request_handler import request_handler


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


@importhook.on_import("quart.app")
def on_quart_import(quart):
    if not pkg_compat_check("quart", required_version=ANY_VERSION):
        return quart
    modified_quart = importhook.copy_module(quart)

    former_handle_request = copy.deepcopy(quart.Quart.handle_request)
    call_original = copy.deepcopy(quart.Quart.__call__)

    async def aikido_handle_request(quart_app, request):
        return await handle_request_wrapper(former_handle_request, quart_app, request)

    # pylint:disable=no-member # Pylint has issues with the wrapping
    setattr(modified_quart.Quart, "__call__", asgi_decorator(call_original, "quart"))
    setattr(modified_quart.Quart, "handle_request", aikido_handle_request)
    return modified_quart
