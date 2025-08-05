import os

import pytest
import aikido_zen.sinks.mistralai

from aikido_zen.thread.thread_cache import get_cache

skip_no_api_key = pytest.mark.skipif(
    "MISTRAL_API_KEY" not in os.environ,
    reason="MISTRAL_API_KEY environment variable not set",
)


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


@pytest.fixture
def mistral():
    import mistralai

    return mistralai.Mistral(api_key=os.getenv("MISTRAL_API_KEY", ""))


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


@skip_no_api_key
def test_mistralai_chat_complete(mistral):
    response = mistral.chat.complete(
        model="mistral-small-latest",  # Specify the Mistralai model
        max_tokens=20,
        messages=[
            {
                "role": "user",
                "content": "Write the longest response possible, just as I am writing a long content",
            }
        ],
    )
    print(response)

    assert get_ai_stats()[0]["model"] == "mistral-small-latest"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "mistralai"
    assert get_ai_stats()[0]["tokens"]["input"] == 17
    assert get_ai_stats()[0]["tokens"]["output"] == 20
    assert get_ai_stats()[0]["tokens"]["total"] == 37


@skip_no_api_key
def test_mistralai_agents_complete(mistral):
    res = mistral.agents.complete(
        max_tokens=11,
        messages=[
            {
                "content": "Who is the best French painter? Answer in one short sentence.",
                "role": "user",
            },
        ],
        agent_id="ag:e1521cc4:20250805:untitled-agent:498e0dd8",
    )
    print(res)

    assert get_ai_stats()[0]["model"] == "mistral-medium-latest"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "mistralai"
    assert get_ai_stats()[0]["tokens"]["input"] == 16
    assert get_ai_stats()[0]["tokens"]["output"] == 11
    assert get_ai_stats()[0]["tokens"]["total"] == 27


@skip_no_api_key
def test_mistralai_embeddings_create(mistral):
    res = mistral.embeddings.create(
        model="mistral-embed",
        inputs=[
            "Embed this sentence.",
            "As well as this one.",
        ],
    )
    print(res)

    assert get_ai_stats()[0]["model"] == "mistral-embed"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "mistralai"
    assert get_ai_stats()[0]["tokens"]["input"] == 15
    assert get_ai_stats()[0]["tokens"]["output"] == 0  # Double-checked this
    assert get_ai_stats()[0]["tokens"]["total"] == 15


@skip_no_api_key
def test_mistralai_fim_complete(mistral):
    res = mistral.fim.complete(
        model="codestral-2405", prompt="def", suffix="return a+b", max_tokens=6
    )
    print(res)

    assert get_ai_stats()[0]["model"] == "codestral-2405"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "mistralai"
    assert get_ai_stats()[0]["tokens"]["input"] == 8
    assert get_ai_stats()[0]["tokens"]["output"] == 6
    assert get_ai_stats()[0]["tokens"]["total"] == 14
