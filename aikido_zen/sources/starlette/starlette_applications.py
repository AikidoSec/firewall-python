"""Wraps starlette.applications to create a context object and run the on_init_handler"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
from aikido_zen.context import Context
from ..functions.on_init_handler import on_init_handler


@importhook.on_import("starlette.applications")
def on_starlette_import(starlette):
    """
    Hook 'n wrap on `starlette.applications`
    Our goal is to wrap the __call__ function of the Starlette class, so we can create a Context object.
    """
    modified_starlette = importhook.copy_module(starlette)
    former_call = copy.deepcopy(starlette.Starlette.__call__)

    async def aikido___call__(app, scope, receive=None, send=None):
        return await aik_call_wrapper(former_call, app, scope, receive, send)

    setattr(modified_starlette.Starlette, "__call__", aikido___call__)
    return modified_starlette


async def aik_call_wrapper(former_call, app, scope, receive, send):
    """Aikido's __call__ wrapper"""
    try:
        if scope["type"] != "http":
            return await former_call(app, scope, receive, send)
        context = Context(req=scope, source="starlette")
        on_init_handler(context)
    except Exception as e:
        logger.debug("Exception on aikido __call__ function : %s", e)
    return await former_call(app, scope, receive, send)
