from ...sinks import on_import, patch_function
from ..starlette.starlette_routing import _request_response


@on_import("fastapi.routing", "fastapi")
def patch(m):
    """
    patching module fastapi.routing
    - patches: request_response

    Newer FastAPI defines its own request_response rather than importing from
    starlette.routing, so the starlette patch alone doesn't cover APIRoute endpoints.
    In older versions FastAPI imports from starlette, so we skip to avoid double-wrapping.
    """
    import starlette.routing

    if m.request_response is not starlette.routing.request_response:
        patch_function(m, "request_response", _request_response)
