"""
patching module requests, when AIKIDO_FEATURE_AI_NETWORK_CAPTURE is on
- patches Session.send, to inspect finished AI API responses
"""

from urllib.parse import urlsplit

from aikido_zen.helpers.ai_network_capture import (
    inspect_ai_response,
    is_ai_network_capture_enabled,
)
from aikido_zen.sinks import on_import, patch_function, after


@after
def _send(func, instance, args, kwargs, return_value):
    # _content holds the decoded body, or False when the response is streamed.
    body = getattr(return_value, "_content", None)
    # Only a read POST response can be counted, so the others skip the URL parsing.
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
