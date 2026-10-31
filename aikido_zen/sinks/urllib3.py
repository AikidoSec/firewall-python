"""
patching module urllib3
- patches HTTPConnectionPool.urlopen, to inspect finished AI API responses
"""

from urllib.parse import urlsplit

from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.inspect_llm_response import inspect_llm_response
from aikido_zen.sinks import on_import, patch_function, after


@after
def _urlopen(func, instance, args, kwargs, return_value):
    # Only preload_content=True stores the body; requests passes False, so its
    # responses are counted in Session.send instead.
    inspect_llm_response(
        return_value,
        method=(get_argument(args, kwargs, 0, "method") or "").upper(),
        host=instance.host,
        path=urlsplit(get_argument(args, kwargs, 1, "url") or "").path,
        status=return_value.status,
        body=getattr(return_value, "_body", None),
        operation="urllib3.HTTPConnectionPool.urlopen",
    )


@on_import("urllib3.connectionpool")
def patch(m):
    patch_function(m, "HTTPConnectionPool.urlopen", _urlopen)
