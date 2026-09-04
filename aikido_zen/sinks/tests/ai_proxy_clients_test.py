import anthropic
import httpx
import openai
import pytest

import aikido_zen.sinks.ai_proxy_clients  # noqa: F401 -- installs the patch
from aikido_zen.ai_proxy.transport import LazyZenAsyncTransport, LazyZenTransport


def mounted_transport(client):
    mounts = client._client._mounts
    assert len(mounts) == 1, mounts
    return next(iter(mounts.values()))


def test_anthropic_sync_client_gets_lazy_transport_by_default():
    client = anthropic.Anthropic(api_key="sk-ant-fake")
    assert isinstance(mounted_transport(client), LazyZenTransport)


@pytest.mark.asyncio
async def test_anthropic_async_client_gets_lazy_transport_by_default():
    client = anthropic.AsyncAnthropic(api_key="sk-ant-fake")
    assert isinstance(mounted_transport(client), LazyZenAsyncTransport)


def test_openai_sync_client_gets_lazy_transport_by_default():
    client = openai.OpenAI(api_key="sk-fake")
    assert isinstance(mounted_transport(client), LazyZenTransport)


@pytest.mark.asyncio
async def test_openai_async_client_gets_lazy_transport_by_default():
    client = openai.AsyncOpenAI(api_key="sk-fake")
    assert isinstance(mounted_transport(client), LazyZenAsyncTransport)


def test_caller_supplied_http_client_is_left_untouched():
    own_transport = httpx.HTTPTransport()
    own_client = anthropic.DefaultHttpxClient(transport=own_transport)

    client = anthropic.Anthropic(api_key="sk-ant-fake", http_client=own_client)

    assert client._client is own_client
