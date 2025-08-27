import json
import os
import aikido_zen.sinks.botocore
import pytest

from aikido_zen.thread.thread_cache import get_cache

skip_no_api_key = pytest.mark.skipif(
    "AWS_BEDROCK_TEST" not in os.environ,
    reason="AWS_BEDROCK_TEST environment variable not set, run `export AWS_BEDROCK_TEST=1`",
)


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


@pytest.fixture
def client():
    import boto3

    client = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
    return client


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


@skip_no_api_key
def test_boto3_converse(client):
    metadata = {
        "model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "prompt": "Are tomatoes a fruit?",
        "max_tokens": 20,
    }

    response = client.converse(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=[{"role": "user", "content": [{"text": metadata["prompt"]}]}],
        inferenceConfig={
            "temperature": 0.7,
            "topP": 0.9,
            "maxTokens": metadata["max_tokens"],
        },
    )
    output = response["output"]["message"]["content"][0]["text"]

    assert get_ai_stats()[0]["model"] == "anthropic.claude-3-sonnet-20240229-v1:0"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "bedrock"
    assert get_ai_stats()[0]["tokens"]["input"] == 13
    assert get_ai_stats()[0]["tokens"]["output"] == 20
    assert get_ai_stats()[0]["tokens"]["total"] == 33


@skip_no_api_key
def test_boto3_invoke_model_claude_3_sonnet(client):
    model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"  # Example model ID for Amazon Bedrock
    input_payload = {
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Are tomatoes a vegetable?"}],
            }
        ],
        "max_tokens": 20,
        "anthropic_version": "bedrock-2023-05-31",
    }
    response = client.invoke_model(modelId=model_id, body=json.dumps(input_payload))
    print(response)
    stats = get_ai_stats()[0]
    assert stats["model"] == "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    assert stats["calls"] == 1
    assert stats["provider"] == "bedrock"
    assert stats["tokens"]["input"] == 14
    assert stats["tokens"]["output"] == 20
    assert stats["tokens"]["total"] == 34
