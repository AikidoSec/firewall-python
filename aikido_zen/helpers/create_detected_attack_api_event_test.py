import pytest
from unittest.mock import MagicMock
from .create_detected_attack_api_event import create_detected_attack_api_event
from aikido_zen.context import Context
import aikido_zen.test_utils as test_utils


def test_create_attack_event_with_long_payload():
    long_payload = "x" * 5000  # Create a payload longer than 4096 characters
    attack = {
        "payload": long_payload,
        "metadata": {"test": "1"},
    }

    event = create_detected_attack_api_event(
        attack=attack,
        context=test_utils.generate_context(),
        blocked=False,
        stack=None,
    )

    assert len(event["attack"]["payload"]) == 4096  # Ensure payload is truncated


def test_create_attack_event_with_long_metadata():
    long_metadata = "x" * 5000  # Create metadata longer than 4096 characters
    attack = {
        "payload": {},
        "metadata": {"test": long_metadata},
    }

    event = create_detected_attack_api_event(
        attack=attack,
        context=test_utils.generate_context(),
        blocked=False,
        stack=None,
    )

    assert event["attack"]["metadata"]["test"] == long_metadata[:4096]


def test_create_attack_event_success():
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }

    event = create_detected_attack_api_event(
        attack=attack,
        context=test_utils.generate_context(),
        blocked=False,
        stack=None,
    )
    assert event == {
        "attack": {
            "blocked": False,
            "metadata": {},
            "payload": '{"key": "value"}',
            "stack": None,
            "user": None,
        },
        "request": {
            "ipAddress": "1.1.1.1",
            "method": "POST",
            "route": "/",
            "source": "flask",
            "url": "http://localhost:8080/",
            "userAgent": None,
        },
        "type": "detected_attack",
    }


def test_create_attack_event_with_blocked_and_stack():
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }
    blocked = True
    stack = "sample stack trace"

    event = create_detected_attack_api_event(
        attack=attack,
        context=test_utils.generate_context(),
        blocked=blocked,
        stack=stack,
    )

    # Check that the attack dictionary has the blocked and stack fields set
    assert event["attack"]["blocked"] is True
    assert event["attack"]["stack"] == stack


def test_create_attack_event_request_data_and_attack_data():
    attack = {
        "payload": {"key": "value"},
        "metadata": {"test": "true"},
    }

    event = create_detected_attack_api_event(
        attack=attack,
        context=test_utils.generate_context(
            method="GET",
            url="http://localhost:8080/hello",
            ip="198.51.100.23",
            route="/hello",
            headers={"user-agent": "Mozilla/5.0"},
        ),
        blocked=False,
        stack=None,
    )

    # Verify the request attribute in the payload
    request_data = event["request"]

    assert request_data["method"] == "GET"
    assert request_data["url"] == "http://localhost:8080/hello"
    assert request_data["ipAddress"] == "198.51.100.23"
    assert not "body" in request_data
    assert not "headers" in request_data
    assert request_data["source"] == "flask"
    assert request_data["route"] == "/hello"
    assert request_data["userAgent"] == "Mozilla/5.0"

    attack_data = event["attack"]
    assert attack_data["blocked"] == False
    assert attack_data["metadata"] == {"test": "true"}
    assert attack_data["payload"] == '{"key": "value"}'
    assert attack_data["stack"] is None
    assert attack_data["user"] is None


def test_create_attack_event_with_user():
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }

    event = create_detected_attack_api_event(
        attack=attack,
        context=test_utils.generate_context(user="test_user"),
        blocked=False,
        stack=None,
    )

    # Verify the user is included in the attack data
    assert event["attack"]["user"] == "test_user"


def test_create_attack_event_no_context_and_attack_data():
    attack = {
        "payload": {"key": "value"},
        "metadata": {"test": "true"},
    }

    event = create_detected_attack_api_event(
        attack=attack,
        context=None,
        blocked=False,
        stack=None,
    )

    # Verify the request attribute in the payload
    request_data = event["request"]
    attack_data = event["attack"]

    assert request_data is None
    assert attack_data["user"] is None

    assert attack_data["blocked"] == False
    assert attack_data["metadata"] == {"test": "true"}
    assert attack_data["payload"] == '{"key": "value"}'
    assert attack_data["stack"] is None
