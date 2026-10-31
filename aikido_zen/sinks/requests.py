"""
patching module requests
- patches Session.send, to inspect finished AI API responses
"""

from urllib.parse import urlsplit

from aikido_zen.helpers.inspect_llm_response import inspect_llm_response
from aikido_zen.sinks import on_import, patch_function, after


@after
def _send(func, instance, args, kwargs, return_value):
    # _content holds the decoded body, or False when the response is streamed.
    body = getattr(return_value, "_content", None)
    url = urlsplit(return_value.url)
    inspect_llm_response(
        return_value,
        method=return_value.request.method,
        host=url.hostname,
        path=url.path,
        status=return_value.status_code,
        body=body if isinstance(body, bytes) else None,
        operation="requests.Session.send",
    )


@on_import("requests")
def patch(m):
    patch_function(m, "Session.send", _send)
