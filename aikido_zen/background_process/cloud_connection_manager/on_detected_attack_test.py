import pytest
from unittest.mock import MagicMock
from .on_detected_attack import on_detected_attack
from ...context import Context
import aikido_zen.test_utils as test_utils


@pytest.fixture
def mock_connection_manager():
    connection_manager = MagicMock()
    connection_manager.token = "test_token"
    connection_manager.block = True
    connection_manager.timeout_in_sec = 5
    connection_manager.api.report = MagicMock(return_value={"status": "success"})
    connection_manager.get_manager_info = lambda: {}
    return connection_manager


def test_on_detected_attack_no_token():
    connection_manager = MagicMock()
    connection_manager.token = None

    on_detected_attack(
        connection_manager,
        attack={},
        context=test_utils.generate_context(),
        blocked=False,
        stack=None,
    )

    connection_manager.api.report.assert_not_called()


def test_on_detected_attack_with_long_payload(mock_connection_manager):
    long_payload = "x" * 5000  # Create a payload longer than 4096 characters
    attack = {
        "payload": long_payload,
        "metadata": {"test": "1"},
    }

    on_detected_attack(
        mock_connection_manager,
        attack=attack,
        context=test_utils.generate_context(),
        blocked=False,
        stack=None,
    )

    assert len(attack["payload"]) == 4096  # Ensure payload is truncated
    mock_connection_manager.api.report.assert_called_once()


def test_on_detected_attack_with_long_metadata(mock_connection_manager):
    long_metadata = "x" * 5000  # Create metadata longer than 4096 characters
    attack = {
        "payload": {},
        "metadata": {"test": long_metadata},
    }

    on_detected_attack(
        mock_connection_manager,
        attack=attack,
        context=test_utils.generate_context(),
        blocked=False,
        stack=None,
    )

    assert attack["metadata"]["test"] == long_metadata[:4096]
    mock_connection_manager.api.report.assert_called_once()


def test_on_detected_attack_success(mock_connection_manager):
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }

    on_detected_attack(
        mock_connection_manager,
        attack=attack,
        context=test_utils.generate_context(),
        blocked=False,
        stack=None,
    )
    assert mock_connection_manager.api.report.call_count == 1


def test_on_detected_attack_exception_handling(mock_connection_manager, caplog):
    attack = {
        "payload": {"key": "value"},
        "metadata": {"key": "value"},
    }

    # Simulate an exception during the API call
    mock_connection_manager.api.report.side_effect = Exception("API error")

    on_detected_attack(
        mock_connection_manager,
        attack=attack,
        context=test_utils.generate_context(),
        blocked=False,
        stack=None,
    )

    assert "Failed to report an attack" in caplog.text


def test_on_detected_attack_with_blocked_and_stack(mock_connection_manager):
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }
    blocked = True
    stack = "sample stack trace"

    on_detected_attack(
        mock_connection_manager,
        attack=attack,
        context=test_utils.generate_context(),
        blocked=blocked,
        stack=stack,
    )

    # Check that the attack dictionary has the blocked and stack fields set
    assert attack["blocked"] is True
    assert attack["stack"] == stack
    assert mock_connection_manager.api.report.call_count == 1


def test_on_detected_attack_request_data_and_attack_data(mock_connection_manager):
    attack = {
        "payload": {"key": "value"},
        "metadata": {"test": "true"},
    }

    on_detected_attack(
        mock_connection_manager,
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

    # Extract the call arguments for the report method
    _, event, _ = mock_connection_manager.api.report.call_args[0]

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


def test_on_detected_attack_with_user(mock_connection_manager):
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }

    on_detected_attack(
        mock_connection_manager,
        attack=attack,
        context=test_utils.generate_context(user="test_user"),
        blocked=False,
        stack=None,
    )

    # Extract the call arguments for the report method
    _, event, _ = mock_connection_manager.api.report.call_args[0]

    # Verify the user is included in the attack data
    assert event["attack"]["user"] == "test_user"


def test_on_detected_attack_no_context_and_attack_data(mock_connection_manager):
    attack = {
        "payload": {"key": "value"},
        "metadata": {"test": "true"},
    }

    on_detected_attack(
        mock_connection_manager,
        attack=attack,
        context=None,
        blocked=False,
        stack=None,
    )

    # Extract the call arguments for the report method
    _, event, _ = mock_connection_manager.api.report.call_args[0]

    # Verify the request attribute in the payload
    request_data = event["request"]
    attack_data = event["attack"]

    assert request_data is None
    assert attack_data["user"] is None

    assert attack_data["blocked"] == False
    assert attack_data["metadata"] == {"test": "true"}
    assert attack_data["payload"] == '{"key": "value"}'
    assert attack_data["stack"] is None
