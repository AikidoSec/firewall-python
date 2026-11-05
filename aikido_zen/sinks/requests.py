from urllib.parse import urlsplit

from aikido_zen.helpers.ai_network_capture import (
    inspect_ai_response,
    is_ai_network_capture_enabled,
)
from aikido_zen.sinks import on_import, patch_function, after


@after
def _send(func, instance, args, kwargs, return_value):
    # _content is False for a streamed response.
    body = getattr(return_value, "_content", None)
    if not isinstance(body, bytes) or return_value.request.method != "POST":
        return
    url = urlsplit(return_value.url)
    inspect_ai_response(
        return_value,
        method=return_value.request.method,
        scheme=url.scheme,
        host=url.hostname,
        port=url.port,
        path=url.path,
        status=return_value.status_code,
        body=body,
    )


@on_import("requests")
def patch(m):
    if is_ai_network_capture_enabled():
        patch_function(m, "Session.send", _send)
