import pytest
from unittest.mock import Mock, patch
from aikido_zen.background_process.heartbeats import send_heartbeats_every_x_secs


def test_send_heartbeats_serverless():
    connection_manager = Mock()
    connection_manager.serverless = True
    connection_manager.token = "mocked_token"
    event_scheduler = Mock()

    with patch("aikido_zen.helpers.logging.logger.debug") as mock_debug:
        send_heartbeats_every_x_secs(connection_manager, 5, event_scheduler)

    mock_debug.assert_called_once_with(
        "Running in serverless environment, not starting heartbeats"
    )
    event_scheduler.enter.assert_not_called()


def test_send_heartbeats_no_token():
    connection_manager = Mock()
    connection_manager.serverless = False
    connection_manager.token = None
    event_scheduler = Mock()

    with patch("aikido_zen.helpers.logging.logger.debug") as mock_debug:
        send_heartbeats_every_x_secs(connection_manager, 5, event_scheduler)

    mock_debug.assert_called_once_with("No token provided, not starting heartbeats")
    event_scheduler.enter.assert_not_called()


def test_send_heartbeats_success():
    connection_manager = Mock()
    connection_manager.serverless = False
    connection_manager.token = "mocked_token"
    event_scheduler = Mock()

    with patch("aikido_zen.helpers.logging.logger.debug") as mock_debug:
        send_heartbeats_every_x_secs(connection_manager, 5, event_scheduler)
