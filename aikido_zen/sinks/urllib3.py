from urllib.parse import urlsplit

from aikido_zen.helpers.ai_network_capture import (
    inspect_ai_response,
    is_ai_network_capture_enabled,
)
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, patch_function, after


@after
def _urlopen(func, instance, args, kwargs, return_value):
    # Only preload_content=True stores the body; requests passes False, so its
    # responses are counted in Session.send instead. botocore passes False too,
    # so its Bedrock calls are counted once, by the botocore sink.
    inspect_ai_response(
        return_value,
        method=(get_argument(args, kwargs, 0, "method") or "").upper(),
        scheme=instance.scheme,
        host=instance.host,
        port=instance.port,
        path=urlsplit(get_argument(args, kwargs, 1, "url") or "").path,
        status=return_value.status,
        body=getattr(return_value, "_body", None),
    )


@on_import("urllib3.connectionpool")
def patch(m):
    if is_ai_network_capture_enabled():
        patch_function(m, "HTTPConnectionPool.urlopen", _urlopen)
