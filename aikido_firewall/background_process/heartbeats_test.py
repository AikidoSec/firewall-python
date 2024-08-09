import pytest
from unittest.mock import Mock, patch
from aikido_firewall.background_process.heartbeats import (
    send_heartbeats_every_x_secs,
    send_heartbeat_wrapper,
)


def test_send_heartbeats_serverless():
    reporter = Mock()
    reporter.serverless = True
    reporter.token = "mocked_token"
    event_scheduler = Mock()

    with patch("aikido_firewall.helpers.logging.logger.debug") as mock_debug:
        send_heartbeats_every_x_secs(reporter, 5, event_scheduler)

    mock_debug.assert_called_once_with(
        "Running in serverless environment, not starting heartbeats"
    )
    event_scheduler.enter.assert_not_called()


def test_send_heartbeats_no_token():
    reporter = Mock()
    reporter.serverless = False
    reporter.token = None
    event_scheduler = Mock()

    with patch("aikido_firewall.helpers.logging.logger.debug") as mock_debug:
        send_heartbeats_every_x_secs(reporter, 5, event_scheduler)

    mock_debug.assert_called_once_with("No token provided, not starting heartbeats")
    event_scheduler.enter.assert_not_called()


def test_send_heartbeats_success():
    reporter = Mock()
    reporter.serverless = False
    reporter.token = "mocked_token"
    event_scheduler = Mock()

    with patch("aikido_firewall.helpers.logging.logger.debug") as mock_debug:
        send_heartbeats_every_x_secs(reporter, 5, event_scheduler)


def test_send_heartbeat_wrapper():
    reporter = Mock()
    reporter.send_heartbeat = Mock()
    event_scheduler = Mock()

    send_heartbeat_wrapper(reporter, 5, event_scheduler)

    reporter.send_heartbeat.assert_called_once()
    event_scheduler.enter.assert_called_once_with(
        5, 1, send_heartbeat_wrapper, (reporter, 5, event_scheduler)
    )
