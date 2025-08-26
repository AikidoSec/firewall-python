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
        "max_tokens": 500,
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

    # Extract and print the response
    output = response["output"]["message"]["content"][0]["text"]
    print(output)
