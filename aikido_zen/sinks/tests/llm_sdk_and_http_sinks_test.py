import asyncio
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor

import pydantic
import pytest

import aikido_zen.sinks.openai
import aikido_zen.sinks.anthropic
import aikido_zen.sinks.mistralai
import aikido_zen.sinks.botocore
import aikido_zen.sinks.httpx
import aikido_zen.sinks.httpx2
import aikido_zen.sinks.urllib3
import aikido_zen.helpers.inspect_llm_response
from aikido_zen.thread.thread_cache import get_cache
from .llm_http_test import BEDROCK_MODEL, BODIES, VERTEX_PATH, provider

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
HTTP = pytest.param("http", id="http")
HTTP_SINK_MISSED = pytest.param("missed", id="http-sink-missed")
HTTP_WITH_FALLBACK = pytest.param("http+fallback", id="http-with-sdk-fallback")
SDK_FALLBACK = pytest.param("fallback", id="http-sink-missed-with-sdk-fallback")


def live_param(env_var):
    return pytest.param(
        "live",
        id="live",
        marks=pytest.mark.skipif(
            env_var not in os.environ, reason=f"{env_var} not set"
        ),
    )


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.delenv("AIKIDO_FEATURE_AI_SDK_FALLBACK", raising=False)
    get_cache().reset()
    yield
    get_cache().reset()


@pytest.fixture
def recorded(monkeypatch):
    calls = []
    ai_stats = get_cache().ai_stats
    original = ai_stats.on_ai_call

    def record(provider_name, model, input_tokens, output_tokens, *cache_tokens):
        calls.append((provider_name, model, input_tokens, output_tokens))
        original(provider_name, model, input_tokens, output_tokens, *cache_tokens)

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


def enable_sdk_fallback(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_AI_SDK_FALLBACK", "true")


def miss_http(monkeypatch):
    monkeypatch.setattr(
        aikido_zen.helpers.inspect_llm_response, "match_ai_request", lambda *a: None
    )


def base_url(mode, provider, monkeypatch, suffix=""):
    if mode in ("http+fallback", "fallback"):
        enable_sdk_fallback(monkeypatch)
    if mode in ("missed", "fallback"):
        miss_http(monkeypatch)
    return None if mode == "live" else provider + suffix


def expected_url(mode, provider, official, path):
    return (official if mode == "live" else provider) + path


@pytest.mark.parametrize(
    "mode",
    [HTTP, HTTP_WITH_FALLBACK, SDK_FALLBACK, live_param("OPENAI_API_KEY")],
)
def test_openai_chat_completions_counted_once(provider, recorded, monkeypatch, mode):
    import openai

    client = openai.OpenAI(
        api_key=None if mode == "live" else "test",
        base_url=base_url(mode, provider, monkeypatch, "/v1"),
        max_retries=0,
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=HELLO, max_tokens=5
    )
    usage = response.usage
    assert recorded == [
        (
            expected_url(
                mode, provider, "https://api.openai.com", "/v1/chat/completions"
            ),
            response.model,
            usage.prompt_tokens,
            usage.completion_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "fallback")


@pytest.mark.parametrize(
    "mode",
    [HTTP, HTTP_WITH_FALLBACK, SDK_FALLBACK, live_param("OPENAI_API_KEY")],
)
def test_openai_responses_counted_once(provider, recorded, monkeypatch, mode):
    import openai

    client = openai.OpenAI(
        api_key=None if mode == "live" else "test",
        base_url=base_url(mode, provider, monkeypatch, "/v1"),
        max_retries=0,
    )
    response = client.responses.create(
        model="gpt-4o-mini", input="Say hi", max_output_tokens=16
    )
    usage = response.usage
    assert recorded == [
        (
            expected_url(mode, provider, "https://api.openai.com", "/v1/responses"),
            response.model,
            usage.input_tokens,
            usage.output_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "fallback")


@pytest.mark.parametrize("mode", [HTTP_WITH_FALLBACK, SDK_FALLBACK])
def test_response_without_id_counted_once(provider, recorded, monkeypatch, mode):
    import openai

    client = openai.OpenAI(
        api_key="test",
        base_url=base_url(mode, provider, monkeypatch, "/v1"),
        max_retries=0,
    )
    for _ in range(2):
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=HELLO, extra_query={"no-id": "1"}
        )
    assert response.id is None
    assert [r[0] for r in recorded] == [provider + "/v1/chat/completions"] * 2
    assert get_cache().ai_stats.get_stats()[0]["calls"] == 2
    assert len(ai_operations()) == 1


class Answer(pydantic.BaseModel):
    text: str


def openai_parse(client):
    completions = client.chat.completions
    parse = getattr(completions, "parse", None) or client.beta.chat.completions.parse
    return parse(model="gpt-4o-mini", messages=HELLO, response_format=Answer)


@pytest.mark.parametrize("mode", [HTTP, HTTP_WITH_FALLBACK, SDK_FALLBACK])
def test_openai_chat_completions_parse_counted_once(
    provider, recorded, monkeypatch, mode
):
    import openai

    monkeypatch.setitem(BODIES, "/v1/chat/completions", STRUCTURED_COMPLETION)
    client = openai.OpenAI(
        api_key="test",
        base_url=base_url(mode, provider, monkeypatch, "/v1"),
        max_retries=0,
    )
    assert openai_parse(client).choices[0].message.parsed.text == "hi"
    assert [r[0] for r in recorded] == [provider + "/v1/chat/completions"]
    assert len(ai_operations()) == 1


@pytest.mark.parametrize("mode", [HTTP, HTTP_WITH_FALLBACK, SDK_FALLBACK])
def test_openai_async_counted_once(provider, recorded, monkeypatch, mode):
    import openai

    client = openai.AsyncOpenAI(
        api_key="test",
        base_url=base_url(mode, provider, monkeypatch, "/v1"),
        max_retries=0,
    )

    async def create_both():
        await client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
        await client.responses.create(model="gpt-4o-mini", input="Say hi")

    asyncio.run(create_both())
    assert [r[0] for r in recorded] == [
        provider + "/v1/chat/completions",
        provider + "/v1/responses",
    ]
    assert ai_operation_total() == 2


@pytest.mark.parametrize("mode", [HTTP, HTTP_SINK_MISSED])
def test_sdk_fallback_is_off_by_default(provider, recorded, monkeypatch, mode):
    import anthropic
    import openai

    client = openai.OpenAI(
        api_key="test",
        base_url=base_url(mode, provider, monkeypatch, "/v1"),
        max_retries=0,
    )
    client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
    client.responses.create(model="gpt-4o-mini", input="Say hi")
    anthropic.Anthropic(
        api_key="test", base_url=provider, max_retries=0
    ).messages.create(model="claude-haiku-4-5", max_tokens=5, messages=HELLO)
    if mode == "missed":
        assert recorded == []
    else:
        assert len(recorded) == 3
        assert counted_by_http_sink()


@pytest.mark.parametrize("is_async", [False, True])
def test_sdk_method_calling_another_one_counted_once(
    provider, recorded, monkeypatch, is_async
):
    import openai

    base_url("fallback", provider, monkeypatch)
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


def test_completions_update_is_not_counted(provider, recorded, monkeypatch):
    import openai

    enable_sdk_fallback(monkeypatch)
    monkeypatch.setitem(
        BODIES, "/v1/chat/completions/chatcmpl-1", BODIES["/v1/chat/completions"]
    )
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    client.chat.completions.update("chatcmpl-1", metadata={"k": "v"})
    assert recorded == []
    assert ai_operations() == []


def miss_the_next_http_count(monkeypatch):
    # The HTTP client sinks count the direct call, then miss the SDK call that follows.
    real = aikido_zen.helpers.inspect_llm_response.match_ai_request
    seen = []

    def match_once(*args):
        seen.append(args)
        return real(*args) if len(seen) == 1 else None

    monkeypatch.setattr(
        aikido_zen.helpers.inspect_llm_response, "match_ai_request", match_once
    )


def test_earlier_direct_call_does_not_hide_an_sdk_call(provider, recorded, monkeypatch):
    import openai
    import requests

    enable_sdk_fallback(monkeypatch)
    miss_the_next_http_count(monkeypatch)
    requests.post(provider + "/v1/chat/completions?no-id=1", json={})
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    client.chat.completions.create(
        model="gpt-4o-mini", messages=HELLO, extra_query={"no-id": "1"}
    )
    assert [r[0] for r in recorded] == [provider + "/v1/chat/completions"] * 2


def test_earlier_direct_call_does_not_hide_an_async_sdk_call(
    provider, recorded, monkeypatch
):
    import httpx
    import openai

    enable_sdk_fallback(monkeypatch)
    miss_the_next_http_count(monkeypatch)
    client = openai.AsyncOpenAI(
        api_key="test", base_url=provider + "/v1", max_retries=0
    )

    async def direct_then_sdk():
        async with httpx.AsyncClient() as http:
            await http.post(provider + "/v1/chat/completions", json={})
        await client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)

    asyncio.run(direct_then_sdk())
    assert [r[0] for r in recorded] == [provider + "/v1/chat/completions"] * 2


def test_openai_with_raw_response_counted_once(provider, recorded, monkeypatch):
    import openai

    enable_sdk_fallback(monkeypatch)
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    raw = client.chat.completions.with_raw_response.create(
        model="gpt-4o-mini", messages=HELLO
    )
    assert raw.parse().model
    assert len(recorded) == 1


def test_openai_retry_after_server_error_counted_once(provider, recorded, monkeypatch):
    import openai

    enable_sdk_fallback(monkeypatch)
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=1)
    client.chat.completions.create(
        model="gpt-4o-mini", messages=HELLO, extra_query={"fail-once": "retry"}
    )
    assert len(recorded) == 1


def test_concurrent_threads_count_each_call_once(provider, recorded, monkeypatch):
    import openai

    enable_sdk_fallback(monkeypatch)
    other_host = provider.replace("127.0.0.1", "localhost")
    clients = [
        openai.OpenAI(api_key="test", base_url=url + "/v1", max_retries=0)
        for url in (provider, other_host)
    ]

    def create(client):
        return client.chat.completions.create(
            model="gpt-4o-mini", messages=HELLO, extra_query={"delay": "0.05"}
        )

    with ThreadPoolExecutor(8) as pool:
        responses = list(pool.map(create, clients * 4))
    assert sorted(r[0] for r in recorded) == sorted(
        [provider + "/v1/chat/completions"] * 4
        + [other_host + "/v1/chat/completions"] * 4
    )
    assert len({r.id for r in responses}) == 8


def test_concurrent_async_tasks_count_each_call_once(provider, recorded, monkeypatch):
    import openai

    enable_sdk_fallback(monkeypatch)
    client = openai.AsyncOpenAI(
        api_key="test", base_url=provider + "/v1", max_retries=0
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
    [HTTP, HTTP_WITH_FALLBACK, SDK_FALLBACK, live_param("ANTHROPIC_API_KEY")],
)
def test_anthropic_messages_counted_once(provider, recorded, monkeypatch, mode):
    import anthropic

    client = anthropic.Anthropic(
        api_key=None if mode == "live" else "test",
        base_url=base_url(mode, provider, monkeypatch),
        max_retries=0,
    )
    response = client.messages.create(
        model="claude-haiku-4-5", max_tokens=5, messages=HELLO
    )
    usage = response.usage
    assert recorded == [
        (
            expected_url(mode, provider, "https://api.anthropic.com", "/v1/messages"),
            response.model,
            usage.input_tokens,
            usage.output_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "fallback")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode",
    [HTTP, HTTP_WITH_FALLBACK, SDK_FALLBACK, live_param("ANTHROPIC_API_KEY")],
)
async def test_anthropic_async_messages_counted_once(
    provider, recorded, monkeypatch, mode
):
    import anthropic

    client = anthropic.AsyncAnthropic(
        api_key=None if mode == "live" else "test",
        base_url=base_url(mode, provider, monkeypatch),
        max_retries=0,
    )
    response = await client.messages.create(
        model="claude-haiku-4-5", max_tokens=5, messages=HELLO
    )
    usage = response.usage
    assert recorded == [
        (
            expected_url(mode, provider, "https://api.anthropic.com", "/v1/messages"),
            response.model,
            usage.input_tokens,
            usage.output_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "fallback")


@pytest.mark.parametrize("mode", [HTTP, HTTP_WITH_FALLBACK])
def test_anthropic_bedrock_client_counted_once(provider, recorded, monkeypatch, mode):
    import anthropic

    pytest.importorskip("boto3")
    client = anthropic.AnthropicBedrock(
        aws_access_key="test",
        aws_secret_key="test",
        aws_region="us-east-1",
        base_url=base_url(mode, provider, monkeypatch),
        max_retries=0,
    )
    client.messages.create(model=BEDROCK_MODEL, max_tokens=5, messages=HELLO)
    assert recorded == [
        (provider + "/model/" + BEDROCK_MODEL + "/invoke", BEDROCK_MODEL, 21, 12)
    ]
    assert counted_by_http_sink()


@pytest.mark.parametrize("mode", [HTTP, HTTP_WITH_FALLBACK])
def test_anthropic_vertex_client_counted_once(provider, recorded, monkeypatch, mode):
    import anthropic

    client = anthropic.AnthropicVertex(
        region="us-east5",
        project_id="p",
        access_token="test",
        base_url=base_url(mode, provider, monkeypatch, "/v1"),
        max_retries=0,
    )
    response = client.messages.create(
        model="claude-sonnet-4@20250514", max_tokens=5, messages=HELLO
    )
    assert recorded == [
        (
            provider + VERTEX_PATH + "claude-sonnet-4@20250514:rawPredict",
            response.model,
            21,
            12,
        )
    ]
    assert counted_by_http_sink()


def test_boto3_bedrock_call_is_counted_once_by_the_botocore_sink(provider, recorded):
    boto3 = pytest.importorskip("boto3")
    client = boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        endpoint_url=provider,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    response = client.invoke_model(
        modelId=BEDROCK_MODEL,
        body=json.dumps({"messages": HELLO, "max_tokens": 5}),
    )
    assert json.loads(response["body"].read())["model"] == "claude-sonnet-4-20250514"
    assert recorded == [("bedrock", BEDROCK_MODEL, 0, 0)]
    assert ai_operations() == ["botocore.client.InvokeModel"]


@pytest.mark.parametrize(
    "mode",
    [HTTP, HTTP_WITH_FALLBACK, SDK_FALLBACK, live_param("MISTRAL_API_KEY")],
)
def test_mistral_chat_complete_counted_once(provider, recorded, monkeypatch, mode):
    mistralai = pytest.importorskip("mistralai")
    try:
        Mistral = mistralai.Mistral
    except AttributeError:
        from mistralai.client import Mistral

    client = Mistral(
        api_key=os.environ.get("MISTRAL_API_KEY") if mode == "live" else "test",
        server_url=base_url(mode, provider, monkeypatch),
    )
    response = client.chat.complete(
        model="mistral-small-latest", messages=HELLO, max_tokens=5
    )
    usage = response.usage
    sdk_sink_can_hook = importlib.util.find_spec("mistralai.chat") is not None
    if mode == "fallback" and not sdk_sink_can_hook:
        assert recorded == []
        return
    assert recorded == [
        (
            expected_url(
                mode, provider, "https://api.mistral.ai", "/v1/chat/completions"
            ),
            response.model,
            usage.prompt_tokens,
            usage.completion_tokens,
        )
    ]
    assert len(ai_operations()) == 1
    assert counted_by_http_sink() == (mode != "fallback")


def test_sdk_and_http_sinks_report_the_same_url(provider, recorded, monkeypatch):
    import openai

    enable_sdk_fallback(monkeypatch)
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
    miss_http(monkeypatch)
    client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
    assert [r[0] for r in recorded] == [provider + "/v1/chat/completions"] * 2
    assert len(ai_operations()) == 2
    assert get_cache().ai_stats.get_stats()[0]["calls"] == 2
