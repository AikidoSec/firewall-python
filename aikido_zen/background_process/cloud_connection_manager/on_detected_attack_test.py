import pytest
from unittest.mock import MagicMock, patch
from .on_detected_attack import on_detected_attack
from ...context import Context


@pytest.fixture
def mock_connection_manager():
    connection_manager = MagicMock()
    connection_manager.token = "test_token"
    connection_manager.block = True
    connection_manager.timeout_in_sec = 5
    connection_manager.api.report = MagicMock(return_value={"status": "success"})
    connection_manager.get_manager_info = lambda: {}
    return connection_manager


@pytest.fixture
def mock_context():
    basic_wsgi_req = {
        "REQUEST_METHOD": "GET",
        "HTTP_HEADER_1": "header 1 value",
        "HTTP_HEADER_2": "Header 2 value",
        "RANDOM_VALUE": "Random value",
        "HTTP_COOKIE": "sessionId=abc123xyz456;",
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "localhost:8080",
        "PATH_INFO": "/hello",
        "QUERY_STRING": "user=JohnDoe&age=30&age=35",
        "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": "198.51.100.23",
        "HTTP_USER_AGENT": "Mozilla/5.0",
    }

    return Context(req=basic_wsgi_req, body=123, source="django")


def test_on_detected_attack_no_token(mock_context):
    connection_manager = MagicMock()
    connection_manager.token = None
    on_detected_attack(connection_manager, {}, mock_context, blocked=False, stack=None)
    connection_manager.api.report.assert_not_called()


def test_on_detected_attack_with_long_payload(mock_connection_manager, mock_context):
    long_payload = "x" * 5000  # Create a payload longer than 4096 characters
    attack = {
        "payload": long_payload,
        "metadata": {"test": "1"},
    }

    on_detected_attack(
        mock_connection_manager, attack, mock_context, blocked=False, stack=None
    )
    assert len(attack["payload"]) == 4096  # Ensure payload is truncated
    mock_connection_manager.api.report.assert_called_once()


def test_on_detected_attack_with_long_metadata(mock_connection_manager, mock_context):
    long_metadata = "x" * 5000  # Create metadata longer than 4096 characters
    attack = {
        "payload": {},
        "metadata": {"test": long_metadata},
    }

    on_detected_attack(
        mock_connection_manager, attack, mock_context, blocked=False, stack=None
    )

    assert (
        attack["metadata"]["test"] == long_metadata[:4096]
    )  # Ensure metadata is truncated
    mock_connection_manager.api.report.assert_called_once()


def test_on_detected_attack_success(mock_connection_manager, mock_context):
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }

    on_detected_attack(
        mock_connection_manager, attack, mock_context, blocked=False, stack=None
    )
    assert mock_connection_manager.api.report.call_count == 1


def test_on_detected_attack_exception_handling(
    mock_connection_manager, mock_context, caplog
):
    attack = {
        "payload": {"key": "value"},
        "metadata": {"key": "value"},
    }

    # Simulate an exception during the API call
    mock_connection_manager.api.report.side_effect = Exception("API error")

    on_detected_attack(
        mock_connection_manager, attack, mock_context, blocked=False, stack=None
    )

    assert "Failed to report an attack" in caplog.text


def test_on_detected_attack_with_blocked_and_stack(
    mock_connection_manager, mock_context
):
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }
    blocked = True
    stack = "sample stack trace"

    on_detected_attack(
        mock_connection_manager, attack, mock_context, blocked=blocked, stack=stack
    )

    # Check that the attack dictionary has the blocked and stack fields set
    assert attack["blocked"] is True
    assert attack["stack"] == stack
    assert mock_connection_manager.api.report.call_count == 1


def test_on_detected_attack_request_data_and_attack_data(
    mock_connection_manager, mock_context
):
    attack = {
        "payload": {"key": "value"},
        "metadata": {"test": "true"},
    }

    on_detected_attack(
        mock_connection_manager, attack, mock_context, blocked=False, stack=None
    )

    # Extract the call arguments for the report method
    _, event, _ = mock_connection_manager.api.report.call_args[0]

    # Verify the request attribute in the payload
    request_data = event["request"]

    assert request_data["method"] == "GET"
    assert request_data["url"] == "http://localhost:8080/hello"
    assert request_data["ipAddress"] == "198.51.100.23"
    assert request_data["body"] == 123
    assert request_data["headers"] == {
        "CONTENT_TYPE": ["application/json"],
        "USER_AGENT": ["Mozilla/5.0"],
        "COOKIE": ["sessionId=abc123xyz456;"],
        "HEADER_1": ["header 1 value"],
        "HEADER_2": ["Header 2 value"],
        "HOST": ["localhost:8080"],
    }
    assert request_data["source"] == "django"
    assert request_data["route"] == "/hello"
    assert request_data["userAgent"] == "Mozilla/5.0"

    attack_data = event["attack"]
    assert attack_data["blocked"] == False
    assert attack_data["metadata"] == {"test": "true"}
    assert attack_data["payload"] == '{"key": "value"}'
    assert attack_data["stack"] is None
    assert attack_data["user"] is None


def test_on_detected_attack_with_user(mock_connection_manager, mock_context):
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }
    # Simulate a user in the context
    mock_context.user = "test_user"

    on_detected_attack(
        mock_connection_manager, attack, mock_context, blocked=False, stack=None
    )

    # Extract the call arguments for the report method
    _, event, _ = mock_connection_manager.api.report.call_args[0]

    # Verify the user is included in the attack data
    assert event["attack"]["user"] == "test_user"
