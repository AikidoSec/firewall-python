"""Wraps starlette.applications to add the ASGI handler"""

import copy
import aikido_zen.importhook as importhook
from ..asgi import asgi_decorator


@importhook.on_import("starlette.applications")
def on_starlette_import(starlette):
    """
    Hook 'n wrap on `starlette.applications`
    Our goal is to wrap the __call__ function of the Starlette class
    """
    modified_starlette = importhook.copy_module(starlette)
    call_original = copy.deepcopy(starlette.Starlette.__call__)

    setattr(
        modified_starlette.Starlette,
        "__call__",
        asgi_decorator(call_original, "starlette"),
    )
    return modified_starlette
