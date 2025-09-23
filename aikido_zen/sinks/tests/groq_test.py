import os
import pytest
import aikido_zen.sinks.groq
from groq import Groq, AsyncGroq
import asyncio

from aikido_zen.thread.thread_cache import get_cache

skip_no_api_key = pytest.mark.skipif(
    "GROQ_API_KEY" not in os.environ,
    reason="GROQ_API_KEY environment variable not set",
)


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


@skip_no_api_key
def test_groq_messages_create():
    client = Groq()
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Explain the importance of low latency LLMs in 10-15 words.",
            }
        ],
        model="openai/gpt-oss-20b",
        max_completion_tokens=20,
    )
    print(chat_completion.choices[0].message.content)

    assert get_ai_stats()[0]["model"] == "gpt-oss-20b"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "openai"
    assert get_ai_stats()[0]["tokens"]["input"] == 87
    assert get_ai_stats()[0]["tokens"]["output"] == 20
    assert get_ai_stats()[0]["tokens"]["total"] == 107


@skip_no_api_key
@pytest.mark.asyncio
async def test_anthropic_messages_create_async():
    client = AsyncGroq()
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Explain the importance of low latency LLMs in great length.",
            }
        ],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        max_completion_tokens=20,
    )
    print(chat_completion.choices[0].message.content)

    assert get_ai_stats()[0]["model"] == "llama-4-scout-17b-16e-instruct"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "meta-llama"
    assert get_ai_stats()[0]["tokens"]["input"] == 22
    assert get_ai_stats()[0]["tokens"]["output"] == 20
    assert get_ai_stats()[0]["tokens"]["total"] == 42
