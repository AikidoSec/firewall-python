import json
import os
import aikido_zen.sinks.botocore
import pytest
import boto3

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
    client = boto3.client(service_name="bedrock-runtime", region_name="eu-west-1")
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

    assert get_ai_stats()[0]["model"] == "claude-3-sonnet-20240229"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "anthropic"
    assert get_ai_stats()[0]["tokens"]["input"] == 13
    assert get_ai_stats()[0]["tokens"]["output"] == 20
    assert get_ai_stats()[0]["tokens"]["total"] == 33


@skip_no_api_key
def test_boto3_invoke_model_claude_3_sonnet(client):
    model_id = (
        "anthropic.claude-3-sonnet-20240229-v1:0"  # Example model ID for Amazon Bedrock
    )
    input_payload = {
        "inputText": "Hello, how are you?",
        "textGenerationConfig": {"maxTokenCount": 100, "temperature": 0.7},
    }
    response = client.invoke_model(modelId=model_id, body=json.dumps(input_payload))
    stats = get_ai_stats()[0]
    assert stats["model"] == "llama2-70b-chat"
    assert stats["calls"] == 1
    assert stats["provider"] == "meta"
    assert stats["tokens"]["input"] == 0
    assert stats["tokens"]["output"] == 30


@skip_no_api_key
def test_boto3_invoke_model_meta_llama3_8b(client):
    metadata = {
        "model": "meta.llama3-8b-instruct-v1:0",
        "prompt": "Who painted the Mona Lisa?",
        "max_tokens": 20,
    }
    body = {
        "prompt": metadata["prompt"],
        "max_gen_len": metadata["max_tokens"],
        "temperature": 0.5,
    }
    response = client.invoke_model(
        modelId=metadata["model"],
        body=json.dumps(body).encode("utf-8"),
    )
    stats = get_ai_stats()[0]
    assert stats["model"] == "llama3-8b-instruct"
    assert stats["calls"] == 1
    assert stats["provider"] == "meta"
    assert stats["tokens"]["input"] == 3
    assert stats["tokens"]["output"] == 20
