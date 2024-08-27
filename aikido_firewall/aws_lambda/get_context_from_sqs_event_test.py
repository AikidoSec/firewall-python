import pytest
from aikido_firewall.helpers.try_parse_as_json import try_parse_as_json
from .get_context_from_sqs_event import get_context_from_sqs_event


# Mock the try_parse_as_json function
def mock_try_parse_as_json(body):
    if body == '{"valid": "json"}':
        return {"valid": "json"}
    return None


# Use pytest's monkeypatch to replace the original function with the mock
@pytest.fixture(autouse=True)
def mock_json_parsing(monkeypatch):
    monkeypatch.setattr(
        "aikido_firewall.helpers.try_parse_as_json.try_parse_as_json",
        mock_try_parse_as_json,
    )


def test_get_context_from_sqs_event_valid():
    event = {"Records": [{"Body": '{"valid": "json"}'}, {"Body": '{"valid": "json"}'}]}
    expected_output = {
        "url": None,
        "method": None,
        "remote_address": None,
        "body": {
            "Records": [{"body": {"valid": "json"}}, {"body": {"valid": "json"}}],
        },
        "route_params": {},
        "headers": {},
        "query": {},
        "cookies": {},
        "source": "lambda/sqs",
        "route": None,
    }
    assert get_context_from_sqs_event(event) == expected_output


def test_get_context_from_sqs_event_no_records():
    event = {"Records": []}
    expected_output = {
        "url": None,
        "method": None,
        "remote_address": None,
        "body": {
            "Records": [],
        },
        "route_params": {},
        "headers": {},
        "query": {},
        "cookies": {},
        "source": "lambda/sqs",
        "route": None,
    }
    assert get_context_from_sqs_event(event) == expected_output


def test_get_context_from_sqs_event_invalid_json():
    event = {"Records": [{"Body": "invalid json"}, {"Body": '{"valid": "json"}'}]}
    expected_output = {
        "url": None,
        "method": None,
        "remote_address": None,
        "body": {
            "Records": [
                {"body": {"valid": "json"}},
            ],
        },
        "route_params": {},
        "headers": {},
        "query": {},
        "cookies": {},
        "source": "lambda/sqs",
        "route": None,
    }
    assert get_context_from_sqs_event(event) == expected_output


def test_get_context_from_sqs_event_mixed_records():
    event = {
        "Records": [
            {"Body": '{"valid": "json"}'},
            {"Body": "invalid json"},
            {"Body": '{"another": "valid json"}'},
        ]
    }
    expected_output = {
        "url": None,
        "method": None,
        "remote_address": None,
        "body": {
            "Records": [
                {"body": {"valid": "json"}},
                {"body": {"another": "valid json"}},
            ],
        },
        "route_params": {},
        "headers": {},
        "query": {},
        "cookies": {},
        "source": "lambda/sqs",
        "route": None,
    }
    assert get_context_from_sqs_event(event) == expected_output
