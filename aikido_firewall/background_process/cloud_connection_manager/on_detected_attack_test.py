import pytest
from unittest.mock import MagicMock, patch
from .on_detected_attack import on_detected_attack


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
    class Context:
        method = "POST"
        url = "http://example.com/api"
        remote_address = "192.168.1.1"
        body = "test body"
        headers = {"Content-Type": "application/json"}
        source = "test_source"
        route = "test_route"

    return Context()


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
