from aikido_zen.helpers.ai_network_capture import is_ai_network_capture_enabled
from aikido_zen.sinks import on_import
from aikido_zen.sinks.httpx import patch_client


@on_import("httpx2")
def patch(m):
    if is_ai_network_capture_enabled():
        patch_client(m)
