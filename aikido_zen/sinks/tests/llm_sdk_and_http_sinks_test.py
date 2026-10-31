import asyncio
import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor

import pydantic
import pytest

import aikido_zen.sinks.openai
import aikido_zen.sinks.anthropic
import aikido_zen.sinks.mistralai
import aikido_zen.sinks.httpx
import aikido_zen.sinks.httpx2
import aikido_zen.helpers.inspect_llm_response
from aikido_zen.helpers.ai_provider_hosts import PROVIDER_BY_HOST
from aikido_zen.thread.thread_cache import get_cache
from .llm_http_test import BODIES, provider

HELLO = [{"role": "user", "content": "Say hi"}]
STRUCTURED_COMPLETION = {
    "id": "chatcmpl-structured",
    "object": "chat.completion",
    "created": 1,
    "model": "gpt-4o-mini-2024-07-18",
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": '{"text": "hi"}'},
        }
    ],
    "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
}
OFFICIAL_HOST = pytest.param("official", id="official-host")
CUSTOM_HOST = pytest.param("custom", id="custom-host")
HTTP_SINK_MISSED = pytest.param("http-sink-missed", id="http-sink-missed")


def live_param(env_var):
    return pytest.param(
        "live",
        id="live",
        marks=pytest.mark.skipif(
            env_var not in os.environ, reason=f"{env_var} not set"
        ),
    )


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


@pytest.fixture
def recorded(monkeypatch):
    calls = []
    ai_stats = get_cache().ai_stats
    original = ai_stats.on_ai_call

    def record(provider_name, model, input_tokens, output_tokens):
        calls.append((provider_name, model, input_tokens, output_tokens))
        original(provider_name, model, input_tokens, output_tokens)

    monkeypatch.setattr(ai_stats, "on_ai_call", record)
    return calls


def ai_operations():
    operations = get_cache().stats.get_record()["operations"]
    return [op for op, stats in operations.items() if stats["kind"] == "ai_op"]


def ai_operation_total():
    operations = get_cache().stats.get_record()["operations"]
    return sum(
        stats["total"] for stats in operations.values() if stats["kind"] == "ai_op"
    )


def counted_by_http_sink():
    return all(op.endswith("Client.send") for op in ai_operations())


def base_url(mode, provider, provider_name, monkeypatch, suffix=""):
    if mode == "live":
        return None
    if mode == "official":
        monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", provider_name)
    if mode == "http-sink-missed":
        monkeypatch.setattr(
            aikido_zen.helpers.inspect_llm_response, "match_ai_request", None
        )
    return provider + suffix


def expected_provider(mode, official_name, custom_name):
    return custom_name if mode in ("custom", "http-sink-missed") else official_name


@pytest.mark.parametrize(
    "mode",
    [OFFICIAL_HOST, CUSTOM_HOST, HTTP_SINK_MISSED, live_param("OPENAI_API_KEY")],
)
def test_openai_chat_completions_counted_once(provider, recorded, monkeypatch, mode):
    import openai

    client = openai.OpenAI(
        api_key=None if mode == "live" else "test",
        base_url=base_url(mode, provider, "openai", monkeypatch, "/v1"),
        max_retries=0,
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=HELLO, max_tokens=5
    )
    usage = response.usage
    assert recorded == [
        (
            expected_provider(mode, "openai", "openai_compatible"),
            response.model,
            usage.prompt_tokens,
            usage.completion_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "http-sink-missed")


@pytest.mark.parametrize(
    "mode",
    [OFFICIAL_HOST, CUSTOM_HOST, HTTP_SINK_MISSED, live_param("OPENAI_API_KEY")],
)
def test_openai_responses_counted_once(provider, recorded, monkeypatch, mode):
    import openai

    client = openai.OpenAI(
        api_key=None if mode == "live" else "test",
        base_url=base_url(mode, provider, "openai", monkeypatch, "/v1"),
        max_retries=0,
    )
    response = client.responses.create(
        model="gpt-4o-mini", input="Say hi", max_output_tokens=16
    )
    usage = response.usage
    assert recorded == [
        (
            expected_provider(mode, "openai", "openai_compatible"),
            response.model,
            usage.input_tokens,
            usage.output_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "http-sink-missed")


def test_openai_sdk_pointed_at_groq_counts_once_as_groq(
    provider, recorded, monkeypatch
):
    import openai

    monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", "groq")
    client = openai.OpenAI(
        api_key="test", base_url=provider + "/openai/v1", max_retries=0
    )
    chat = client.chat.completions.create(model="openai/gpt-oss-20b", messages=HELLO)
    response = client.responses.create(model="openai/gpt-oss-20b", input="Say hi")
    assert recorded == [
        ("groq", chat.model, chat.usage.prompt_tokens, chat.usage.completion_tokens),
        (
            "groq",
            response.model,
            response.usage.input_tokens,
            response.usage.output_tokens,
        ),
    ]


@pytest.mark.parametrize("mode", [CUSTOM_HOST, HTTP_SINK_MISSED])
def test_response_without_id_counted_once(provider, recorded, monkeypatch, mode):
    import openai

    client = openai.OpenAI(
        api_key="test",
        base_url=base_url(mode, provider, "openai", monkeypatch, "/v1"),
        max_retries=0,
    )
    for _ in range(2):
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=HELLO, extra_query={"no-id": "1"}
        )
    assert response.id is None
    assert [r[0] for r in recorded] == ["openai_compatible"] * 2
    assert get_cache().ai_stats.get_stats()[0]["calls"] == 2
    assert len(ai_operations()) == 1


class Answer(pydantic.BaseModel):
    text: str


def openai_parse(client):
    completions = client.chat.completions
    parse = getattr(completions, "parse", None) or client.beta.chat.completions.parse
    return parse(model="gpt-4o-mini", messages=HELLO, response_format=Answer)


@pytest.mark.parametrize("mode", [OFFICIAL_HOST, CUSTOM_HOST, HTTP_SINK_MISSED])
def test_openai_chat_completions_parse_counted_once(
    provider, recorded, monkeypatch, mode
):
    import openai

    monkeypatch.setitem(BODIES, "/v1/chat/completions", STRUCTURED_COMPLETION)
    client = openai.OpenAI(
        api_key="test",
        base_url=base_url(mode, provider, "openai", monkeypatch, "/v1"),
        max_retries=0,
    )
    assert openai_parse(client).choices[0].message.parsed.text == "hi"
    assert [r[0] for r in recorded] == [
        expected_provider(mode, "openai", "openai_compatible")
    ]
    assert len(ai_operations()) == 1


@pytest.mark.parametrize("mode", [OFFICIAL_HOST, HTTP_SINK_MISSED])
def test_openai_async_counted_once(provider, recorded, monkeypatch, mode):
    import openai

    client = openai.AsyncOpenAI(
        api_key="test",
        base_url=base_url(mode, provider, "openai", monkeypatch, "/v1"),
        max_retries=0,
    )

    async def create_both():
        await client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
        await client.responses.create(model="gpt-4o-mini", input="Say hi")

    asyncio.run(create_both())
    assert [r[0] for r in recorded] == [
        expected_provider(mode, "openai", "openai_compatible")
    ] * 2
    assert ai_operation_total() == 2


@pytest.mark.parametrize("is_async", [False, True])
def test_sdk_method_calling_another_one_counted_once(
    provider, recorded, monkeypatch, is_async
):
    import openai

    base_url("http-sink-missed", provider, "openai", monkeypatch)
    sdk_ai_call = aikido_zen.helpers.inspect_llm_response.sdk_ai_call
    count_outer = lambda instance, response: get_cache().ai_stats.on_ai_call(
        "outer", "m", 1, 1
    )
    if is_async:
        client = openai.AsyncOpenAI(
            api_key="test", base_url=provider + "/v1", max_retries=0
        )

        async def inner():
            return await client.chat.completions.create(
                model="gpt-4o-mini", messages=HELLO
            )

        asyncio.run(sdk_ai_call(count_outer, is_async=True)(inner, None, (), {}))
    else:
        client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
        inner = lambda: client.chat.completions.create(
            model="gpt-4o-mini", messages=HELLO
        )
        sdk_ai_call(count_outer)(inner, None, (), {})
    assert [r[0] for r in recorded] == ["outer"]


def test_completions_update_counted_once(provider, recorded, monkeypatch):
    import openai

    monkeypatch.setitem(
        BODIES, "/v1/chat/completions/chatcmpl-1", BODIES["/v1/chat/completions"]
    )
    monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", "openai")
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
    client.chat.completions.update("chatcmpl-1", metadata={"k": "v"})
    assert [r[0] for r in recorded] == ["openai", "openai"]
    assert len(ai_operations()) == 2
    assert "openai.resources.chat.completions.completions.Completions.update" in (
        ai_operations()
    )


def test_earlier_direct_call_does_not_hide_an_sdk_call(provider, recorded, monkeypatch):
    import openai
    import requests

    monkeypatch.setitem(
        BODIES, "/v1/chat/completions/chatcmpl-1", BODIES["/v1/chat/completions"]
    )
    requests.post(provider + "/v1/chat/completions?no-id=1", json={})
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    client.chat.completions.update(
        "chatcmpl-1", metadata={"k": "v"}, extra_query={"no-id": "1"}
    )
    assert [r[0] for r in recorded] == ["openai_compatible"] * 2


def test_earlier_direct_call_does_not_hide_an_async_sdk_call(
    provider, recorded, monkeypatch
):
    import httpx
    import openai

    monkeypatch.setitem(
        BODIES, "/v1/chat/completions/chatcmpl-1", BODIES["/v1/chat/completions"]
    )
    client = openai.AsyncOpenAI(
        api_key="test", base_url=provider + "/v1", max_retries=0
    )

    async def direct_then_update():
        async with httpx.AsyncClient() as http:
            await http.post(provider + "/v1/chat/completions", json={})
        await client.chat.completions.update("chatcmpl-1", metadata={"k": "v"})

    asyncio.run(direct_then_update())
    assert [r[0] for r in recorded] == ["openai_compatible"] * 2


def test_openai_with_raw_response_counted_once(provider, recorded, monkeypatch):
    import openai

    monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", "openai")
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    raw = client.chat.completions.with_raw_response.create(
        model="gpt-4o-mini", messages=HELLO
    )
    assert raw.parse().model
    assert len(recorded) == 1


def test_openai_retry_after_server_error_counted_once(provider, recorded, monkeypatch):
    import openai

    monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", "openai")
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=1)
    client.chat.completions.create(
        model="gpt-4o-mini", messages=HELLO, extra_query={"fail-once": "retry"}
    )
    assert len(recorded) == 1


def test_concurrent_threads_count_each_call_once(provider, recorded, monkeypatch):
    import openai

    official = openai.OpenAI(
        api_key="test",
        base_url=base_url("official", provider, "openai", monkeypatch, "/v1"),
        max_retries=0,
    )
    custom = openai.OpenAI(
        api_key="test",
        base_url=provider.replace("127.0.0.1", "localhost") + "/v1",
        max_retries=0,
    )

    def create(client):
        return client.chat.completions.create(
            model="gpt-4o-mini", messages=HELLO, extra_query={"delay": "0.05"}
        )

    with ThreadPoolExecutor(8) as pool:
        responses = list(pool.map(create, [official, custom] * 4))
    assert sorted(r[0] for r in recorded) == ["openai"] * 4 + ["openai_compatible"] * 4
    assert len({r.id for r in responses}) == 8


def test_concurrent_async_tasks_count_each_call_once(provider, recorded, monkeypatch):
    import openai

    client = openai.AsyncOpenAI(
        api_key="test",
        base_url=base_url("official", provider, "openai", monkeypatch, "/v1"),
        max_retries=0,
    )

    async def create_all():
        return await asyncio.gather(
            *[
                client.chat.completions.create(
                    model="gpt-4o-mini", messages=HELLO, extra_query={"delay": "0.05"}
                )
                for _ in range(8)
            ]
        )

    responses = asyncio.run(create_all())
    assert len(recorded) == 8
    assert len({r.id for r in responses}) == 8


@pytest.mark.parametrize(
    "mode",
    [OFFICIAL_HOST, CUSTOM_HOST, HTTP_SINK_MISSED, live_param("ANTHROPIC_API_KEY")],
)
def test_anthropic_messages_counted_once(provider, recorded, monkeypatch, mode):
    import anthropic

    client = anthropic.Anthropic(
        api_key=None if mode == "live" else "test",
        base_url=base_url(mode, provider, "anthropic", monkeypatch),
        max_retries=0,
    )
    response = client.messages.create(
        model="claude-haiku-4-5", max_tokens=5, messages=HELLO
    )
    usage = response.usage
    assert recorded == [
        (
            expected_provider(mode, "anthropic", "anthropic_compatible"),
            response.model,
            usage.input_tokens,
            usage.output_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "http-sink-missed")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode",
    [OFFICIAL_HOST, CUSTOM_HOST, HTTP_SINK_MISSED, live_param("ANTHROPIC_API_KEY")],
)
async def test_anthropic_async_messages_counted_once(
    provider, recorded, monkeypatch, mode
):
    import anthropic

    client = anthropic.AsyncAnthropic(
        api_key=None if mode == "live" else "test",
        base_url=base_url(mode, provider, "anthropic", monkeypatch),
        max_retries=0,
    )
    response = await client.messages.create(
        model="claude-haiku-4-5", max_tokens=5, messages=HELLO
    )
    usage = response.usage
    assert recorded == [
        (
            expected_provider(mode, "anthropic", "anthropic_compatible"),
            response.model,
            usage.input_tokens,
            usage.output_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "http-sink-missed")


@pytest.mark.parametrize(
    "mode",
    [OFFICIAL_HOST, CUSTOM_HOST, HTTP_SINK_MISSED, live_param("MISTRAL_API_KEY")],
)
def test_mistral_chat_complete_counted_once(provider, recorded, monkeypatch, mode):
    mistralai = pytest.importorskip("mistralai")
    try:
        Mistral = mistralai.Mistral
    except AttributeError:
        from mistralai.client import Mistral

    client = Mistral(
        api_key=os.environ.get("MISTRAL_API_KEY") if mode == "live" else "test",
        server_url=base_url(mode, provider, "mistral", monkeypatch),
    )
    response = client.chat.complete(
        model="mistral-small-latest", messages=HELLO, max_tokens=5
    )
    usage = response.usage
    sdk_sink_can_hook = importlib.util.find_spec("mistralai.chat") is not None
    if mode == "http-sink-missed" and not sdk_sink_can_hook:
        assert recorded == []
        return
    assert recorded == [
        (
            expected_provider(mode, "mistral", "openai_compatible"),
            response.model,
            usage.prompt_tokens,
            usage.completion_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "http-sink-missed")


def test_sdk_and_http_sinks_name_the_provider_the_same(provider, recorded, monkeypatch):
    import openai

    monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", "azure")
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
    monkeypatch.setattr(
        aikido_zen.helpers.inspect_llm_response, "match_ai_request", None
    )
    client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
    assert [r[0] for r in recorded] == ["azure", "azure"]
    assert len(ai_operations()) == 2
