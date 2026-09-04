"""
An httpx transport that resolves the local AI proxy lazily, on the first
request, rather than at SDK-client-construction time.

This matters because `openai.OpenAI()` / `anthropic.Anthropic()` are very
often constructed at import time — before the background process has had a
chance to spawn the proxy and publish its runtime file. Falls back to a
direct (unproxied) transport whenever the proxy isn't up, so a dead or slow
proxy never breaks a customer's LLM call.
"""

import threading

import httpx

from .runtime import read_runtime_info

_cache_lock = threading.Lock()
# keyed by (proxy_port, ca_path); reset whenever the proxy restarts on new ports
_cache = {"key": None, "sync": None, "async": None}


def _resolve_key():
    info = read_runtime_info()
    if info is None:
        return None
    return (info["proxy_port"], info["ca_path"])


def _cached_transport(slot, build):
    key = _resolve_key()
    if key is None:
        return None
    with _cache_lock:
        if key != _cache["key"]:
            _cache["key"], _cache["sync"], _cache["async"] = key, None, None
        if _cache[slot] is None:
            port, ca_path = key
            _cache[slot] = build(proxy=f"http://127.0.0.1:{port}", verify=ca_path)
        return _cache[slot]


def _get_sync_transport():
    return _cached_transport("sync", httpx.HTTPTransport)


def _get_async_transport():
    return _cached_transport("async", httpx.AsyncHTTPTransport)


def reset_cache():
    """Test-only: drops the cached transport so the next request re-resolves
    the runtime file instead of reusing a torn-down proxy's connection."""
    with _cache_lock:
        _cache["key"] = _cache["sync"] = _cache["async"] = None


class LazyZenTransport(httpx.BaseTransport):
    """Fails open: any error reaching the local proxy falls back to a direct
    connection rather than breaking the caller's request."""

    def handle_request(self, request):
        transport = _get_sync_transport()
        if transport is not None:
            try:
                return transport.handle_request(request)
            except (httpx.ConnectError, httpx.ConnectTimeout):
                pass
        return httpx.HTTPTransport().handle_request(request)


class LazyZenAsyncTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request):
        transport = _get_async_transport()
        if transport is not None:
            try:
                return await transport.handle_async_request(request)
            except (httpx.ConnectError, httpx.ConnectTimeout):
                pass
        return await httpx.AsyncHTTPTransport().handle_async_request(request)
