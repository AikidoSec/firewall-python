import os

import pytest

import aikido_zen
from aikido_zen.thread.thread_cache import get_cache

aikido_zen.protect(mode="daemon-disabled")

skip_no_openai_key = pytest.mark.skipif(
    "OPENAI_API_KEY" not in os.environ,
    reason="OPENAI_API_KEY environment variable not set",
)
skip_no_anthropic_key = pytest.mark.skipif(
    "ANTHROPIC_API_KEY" not in os.environ,
    reason="ANTHROPIC_API_KEY environment variable not set",
)
skip_no_mistral_key = pytest.mark.skipif(
    "MISTRAL_API_KEY" not in os.environ,
    reason="MISTRAL_API_KEY environment variable not set",
)


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


@skip_no_anthropic_key
def test_langchain_report_tokens_invoke_anthropic():
    from langchain.chat_models import init_chat_model

    llm = init_chat_model("claude-haiku-4-5", model_provider="anthropic", max_tokens=15)
    llm.invoke("Whatsthemattaa").pretty_print()

    assert get_ai_stats()[0]["model"] == "claude-haiku-4-5-20251001"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "anthropic"
    assert get_ai_stats()[0]["tokens"]["input"] == 14
    assert get_ai_stats()[0]["tokens"]["output"] == 15
    assert get_ai_stats()[0]["tokens"]["total"] == 29


@skip_no_mistral_key
def test_langchain_report_tokens_invoke_mistral():
    from langchain.chat_models import init_chat_model

    llm = init_chat_model(
        "mistral-large-latest", model_provider="mistralai", max_tokens=25
    )
    llm.invoke("What is heavier, 10kg of bricks or 10kgs of feathers?").pretty_print()

    assert get_ai_stats()[0]["model"].startswith("mistral-large")
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "mistral"


@skip_no_openai_key
def test_langchain_report_tokens_invoke_openai():
    from langchain.chat_models import init_chat_model

    llm = init_chat_model("gpt-4o-mini", model_provider="openai", max_tokens=20)
    llm.invoke("Whatsthemattaa").pretty_print()

    assert get_ai_stats()[0]["model"] == "gpt-4o-mini-2024-07-18"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "openai"
    assert get_ai_stats()[0]["tokens"]["input"] == 11
    assert get_ai_stats()[0]["tokens"]["output"] == 20
    assert get_ai_stats()[0]["tokens"]["total"] == 31
