import pytest
from .events import is_sqs_event, is_gateway_event


def test_is_sqs_event_valid():
    event = {
        "Records": [
            {
                "messageId": "1",
                "receiptHandle": "abc",
                "body": "Hello from SQS",
                "attributes": {},
                "messageAttributes": {},
                "md5OfBody": "xyz",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
                "awsRegion": "us-east-1",
            }
        ]
    }
    assert is_sqs_event(event) is True


def test_is_sqs_event_invalid_no_records():
    event = {"messageId": "1", "body": "Hello from SQS"}
    assert is_sqs_event(event) is False


def test_is_sqs_event_invalid_not_plain_object():
    event = "This is not an object"
    assert is_sqs_event(event) is False


def test_is_gateway_event_valid():
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": '{"key": "value"}',
    }
    assert is_gateway_event(event) is True


def test_is_gateway_event_invalid_no_http_method():
    event = {
        "headers": {"Content-Type": "application/json"},
        "body": '{"key": "value"}',
    }
    assert is_gateway_event(event) is False


def test_is_gateway_event_invalid_no_headers():
    event = {"httpMethod": "POST", "body": '{"key": "value"}'}
    assert is_gateway_event(event) is False


def test_is_gateway_event_invalid_not_plain_object():
    event = 12345  # Not a plain object
    assert is_gateway_event(event) is False


def test_is_gateway_event_invalid_empty_event():
    event = {}
    assert is_gateway_event(event) is False
