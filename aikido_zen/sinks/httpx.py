from aikido_zen.helpers.ai_network_capture import (
    inspect_ai_response,
    is_ai_network_capture_enabled,
)
from aikido_zen.sinks import on_import, patch_function, after, after_async


def inspect_send(response):
    # No _content means a streamed response, which only the app may read.
    url = response.request.url
    inspect_ai_response(
        response,
        method=response.request.method,
        scheme=url.scheme,
        host=url.host,
        port=url.port,
        # url.path is decoded; raw_path keeps the encoding, as requests and urllib3 do.
        path=url.raw_path.split(b"?", 1)[0].decode("ascii"),
        status=response.status_code,
        body=getattr(response, "_content", None),
    )


@after
def _send(func, instance, args, kwargs, return_value):
    inspect_send(return_value)


@after_async
async def _async_send(func, instance, args, kwargs, return_value):
    inspect_send(return_value)


def patch_client(m):
    patch_function(m, "Client.send", _send)
    patch_function(m, "AsyncClient.send", _async_send)


@on_import("httpx")
def patch(m):
    if is_ai_network_capture_enabled():
        patch_client(m)
