import os

import pytest
import aikido_zen.sinks.anthropic
import anthropic
import asyncio

from aikido_zen.thread.thread_cache import get_cache

skip_no_api_key = pytest.mark.skipif(
    "ANTHROPIC_API_KEY" not in os.environ,
    reason="ANTHROPIC_API_KEY environment variable not set",
)


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


@skip_no_api_key
def test_anthropic_messages_create():
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=20,
        messages=[
            {
                "role": "user",
                "content": "Write the longest response possible, just as I am writing a long content",
            }
        ],
    )
    print(response)

    assert get_ai_stats()[0]["model"] == "claude-sonnet-4-20250514"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "anthropic"
    assert get_ai_stats()[0]["tokens"]["input"] == 21
    assert get_ai_stats()[0]["tokens"]["output"] == 20
    assert get_ai_stats()[0]["tokens"]["total"] == 41


@skip_no_api_key
@pytest.mark.asyncio
async def test_anthropic_messages_create_async():
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=20,
        messages=[
            {
                "role": "user",
                "content": "Write the longest response possible, just as I am writing a long content",
            }
        ],
    )
    print(response)

    assert get_ai_stats()[0]["model"] == "claude-sonnet-4-20250514"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "anthropic"
    assert get_ai_stats()[0]["tokens"]["input"] == 21
    assert get_ai_stats()[0]["tokens"]["output"] == 20
    assert get_ai_stats()[0]["tokens"]["total"] == 41
