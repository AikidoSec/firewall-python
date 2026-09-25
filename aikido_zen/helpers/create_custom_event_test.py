from unittest.mock import MagicMock
from .create_custom_event import (
    create_custom_event,
    extract_request_if_possible,
)
import aikido_zen.test_utils as test_utils


def test_create_custom_event_success():
    """Test successful creation of a custom event with basic data"""
    context = test_utils.generate_context()

    event = create_custom_event("user.login_failed", context)

    assert event is not None
    assert event["type"] == "custom"
    assert event["name"] == "user.login_failed"
    assert event["user"] is None
    assert event["request"] is not None


def test_create_custom_event_with_user():
    """Test custom event creation with user information"""
    context = test_utils.generate_context(user={"id": "user-1", "name": "Jane Doe"})

    event = create_custom_event("user.signed_up", context)

    assert event["user"] == {"id": "user-1", "name": "Jane Doe"}


def test_create_custom_event_request_data():
    """Test that request data is correctly extracted from context"""
    context = test_utils.generate_context(
        ip="198.51.100.23",
        method="POST",
        route="/test-route",
        headers={"user-agent": "Mozilla/5.0"},
    )

    request = create_custom_event("payment.failed", context)["request"]

    assert request["method"] == "POST"
    assert request["ipAddress"] == "198.51.100.23"
    assert request["userAgent"] == "Mozilla/5.0"
    assert request["source"] == "flask"
    assert request["route"] == "/test-route"


def test_create_custom_event_does_not_include_the_url():
    """Unlike a detected attack event, a custom event does not report the url"""
    context = test_utils.generate_context(url="http://localhost:8080/track-me")

    request = create_custom_event("user.login_failed", context)["request"]

    assert "url" not in request


def test_create_custom_event_no_context():
    """Test custom event creation with None context"""
    event = create_custom_event("user.login_failed", None)

    assert event["request"] is None
    assert event["user"] is None


def test_create_custom_event_exception_handling():
    """Test that exceptions during event creation are handled gracefully"""
    context = MagicMock()
    context.get_user_agent.side_effect = Exception("Test exception")

    event = create_custom_event("user.login_failed", context)

    assert event is None


def test_extract_request_if_possible_with_valid_context():
    """Test request extraction with valid context"""
    context = test_utils.generate_context(
        ip="198.51.100.23",
        route="/test-route",
        headers={"user-agent": "Mozilla/5.0"},
    )

    request = extract_request_if_possible(context)

    assert request is not None
    assert request["ipAddress"] == "198.51.100.23"
    assert request["source"] == "flask"
    assert request["userAgent"] == "Mozilla/5.0"


def test_extract_request_if_possible_with_none_context():
    """Test request extraction with None context"""
    request = extract_request_if_possible(None)
    assert request is None


def test_extract_request_if_possible_with_minimal_context():
    """Test request extraction with minimal context data"""
    context = test_utils.generate_context()

    request = extract_request_if_possible(context)

    assert request is not None
    assert request["ipAddress"] == "1.1.1.1"
    assert request["source"] == "flask"
    assert request["userAgent"] is None
