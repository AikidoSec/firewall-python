import os

import pytest
import aikido_zen.sinks.openai

from aikido_zen.thread.thread_cache import get_cache

skip_no_api_key = pytest.mark.skipif(
    "OPENAI_API_KEY" not in os.environ,
    reason="OPENAI_API_KEY environment variable not set",
)


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


@pytest.fixture
def client():
    import openai

    return openai.OpenAI()


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


@skip_no_api_key
def test_openai_responses_create_with_vision(client):
    prompt = "What is in this image?"
    img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/2023_06_08_Raccoon1.jpg/1599px-2023_06_08_Raccoon1.jpg"

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"{img_url}"},
                ],
            }
        ],
        max_output_tokens=25,
    )
    print(response)

    assert get_ai_stats()[0]["model"] == "gpt-4o-mini-2024-07-18"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "openai"
    assert get_ai_stats()[0]["tokens"]["input"] == 36848
    assert get_ai_stats()[0]["tokens"]["output"] == 25
    assert get_ai_stats()[0]["tokens"]["total"] == 36873


@skip_no_api_key
def test_openai_chat_complete(client):
    completion = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=15,
        messages=[
            {"role": "developer", "content": "Talk like a pirate."},
            {
                "role": "user",
                "content": "Who is the best French painter? Answer in one short sentence.",
            },
        ],
    )
    answer = completion.choices[0].message.content
    print(answer)

    assert get_ai_stats()[0]["model"] == "gpt-4o-2024-08-06"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "openai"
    assert get_ai_stats()[0]["tokens"]["input"] == 29
    assert get_ai_stats()[0]["tokens"]["output"] == 15
    assert get_ai_stats()[0]["tokens"]["total"] == 44


@skip_no_api_key
def test_openai_responses_create(client):
    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a coding assistant that talks like a pirate.",
        input="How do I check if a Python object is an instance of a class?",
        max_output_tokens=18,
    )
    print(response.output_text)

    assert get_ai_stats()[0]["model"] == "gpt-4o-2024-08-06"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "openai"
    assert get_ai_stats()[0]["tokens"]["input"] == 37
    assert get_ai_stats()[0]["tokens"]["output"] == 18
    assert get_ai_stats()[0]["tokens"]["total"] == 55
