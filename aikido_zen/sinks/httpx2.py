"""
patching module httpx2, which newer SDKs use instead of httpx (openai 3.x,
anthropic 1.x and later, mistralai 3.x)
- patches Client.send and AsyncClient.send, same as httpx
"""

from aikido_zen.sinks import on_import
from aikido_zen.sinks.httpx import patch_client


@on_import("httpx2")
def patch(m):
    patch_client(m)
