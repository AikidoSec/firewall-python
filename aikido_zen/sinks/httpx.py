"""
patching module httpx
- patches Client.send and AsyncClient.send, to inspect finished AI API responses
"""

from aikido_zen.helpers.inspect_llm_response import inspect_llm_response
from aikido_zen.sinks import on_import, patch_function, after, after_async


def inspect_send(response, operation):
    # No _content means a streamed response, which only the app may read.
    inspect_llm_response(
        response,
        method=response.request.method,
        host=response.request.url.host,
        path=response.request.url.path,
        status=response.status_code,
        body=getattr(response, "_content", None),
        operation=operation,
    )


def patch_client(m):
    """Patches the sync and async clients of httpx, or of httpx2 (same API)"""
    send_op = f"{m.__name__}.Client.send"
    async_send_op = f"{m.__name__}.AsyncClient.send"

    @after
    def _send(func, instance, args, kwargs, return_value):
        inspect_send(return_value, send_op)

    @after_async
    async def _async_send(func, instance, args, kwargs, return_value):
        inspect_send(return_value, async_send_op)

    patch_function(m, "Client.send", _send)
    patch_function(m, "AsyncClient.send", _async_send)


@on_import("httpx")
def patch(m):
    patch_client(m)
