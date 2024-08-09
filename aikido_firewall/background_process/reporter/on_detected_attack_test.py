import pytest
from unittest.mock import MagicMock, patch
from .on_detected_attack import on_detected_attack


@pytest.fixture
def mock_reporter():
    reporter = MagicMock()
    reporter.token = "test_token"
    reporter.block = True
    reporter.timeout_in_sec = 5
    reporter.api.report = MagicMock(return_value={"status": "success"})
    reporter.get_reporter_info = lambda: {}
    return reporter


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
    reporter = MagicMock()
    reporter.token = None
    on_detected_attack(reporter, {}, mock_context)
    reporter.api.report.assert_not_called()


def test_on_detected_attack_with_long_payload(mock_reporter, mock_context):
    long_payload = "x" * 5000  # Create a payload longer than 4096 characters
    attack = {
        "payload": long_payload,
        "metadata": {"test": "1"},
    }

    on_detected_attack(mock_reporter, attack, mock_context)
    assert len(attack["payload"]) == 4096  # Ensure payload is truncated
    mock_reporter.api.report.assert_called_once()


def test_on_detected_attack_with_long_metadata(mock_reporter, mock_context):
    long_metadata = "x" * 5000  # Create metadata longer than 4096 characters
    attack = {
        "payload": {},
        "metadata": {"test": long_metadata},
    }

    on_detected_attack(mock_reporter, attack, mock_context)

    assert (
        attack["metadata"]["test"] == long_metadata[:4096]
    )  # Ensure metadata is truncated
    mock_reporter.api.report.assert_called_once()


def test_on_detected_attack_success(mock_reporter, mock_context):
    attack = {
        "payload": {"key": "value"},
        "metadata": {},
    }

    on_detected_attack(mock_reporter, attack, mock_context)
    assert mock_reporter.api.report.call_count == 1


def test_on_detected_attack_exception_handling(mock_reporter, mock_context, caplog):
    attack = {
        "payload": {"key": "value"},
        "metadata": {"key": "value"},
    }

    # Simulate an exception during the API call
    mock_reporter.api.report.side_effect = Exception("API error")

    on_detected_attack(mock_reporter, attack, mock_context)

    assert "Failed to report attack" in caplog.text
