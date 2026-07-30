import pytest
from unittest.mock import patch, MagicMock
from aikido_zen.helpers.token import Token
from aikido_zen.background_process.api.http_api import ReportingApiHTTP
from aikido_zen.background_process.service_config import ServiceConfig
from aikido_zen.storage.users import Users
from aikido_zen.storage.hostnames import Hostnames
from aikido_zen.ratelimiting.rate_limiter import RateLimiter
from aikido_zen.storage.statistics import Statistics
from . import CloudConnectionManager


@pytest.fixture
def setup_cloud_connection_manager():
    block = None  # Replace with appropriate mock or object if needed
    api = ReportingApiHTTP(None)  # Mock or create an instance of ReportingApiHTTP
    token = Token("AIK_TOKEN_TEST")  # Mock or create an instance of Token
    serverless = "some_value"  # Valid serverless value
    return CloudConnectionManager(block, api, token, serverless)


def test_cloud_connection_manager_initialization(setup_cloud_connection_manager):
    manager = setup_cloud_connection_manager

    # Check that instance variables are initialized correctly
    assert manager.block is None
    assert isinstance(manager.api, ReportingApiHTTP)
    assert isinstance(manager.token, Token)
    assert len(manager.routes) == 0
    assert isinstance(manager.hostnames, Hostnames)
    assert isinstance(manager.conf, ServiceConfig)
    assert isinstance(manager.rate_limiter, RateLimiter)
    assert isinstance(manager.users, Users)
    assert isinstance(manager.statistics, Statistics)
    assert manager.middleware_installed is False
    assert manager.serverless == "some_value"


def test_cloud_connection_manager_empty_serverless():
    block = None  # Replace with appropriate mock or object if needed
    api = ReportingApiHTTP(None)  # Mock or create an instance of ReportingApiHTTP
    token = Token("Hellow")  # Mock or create an instance of Token
    serverless = ""  # Invalid serverless value

    with pytest.raises(ValueError, match="Serverless cannot be an empty string"):
        CloudConnectionManager(block, api, token, serverless)


@patch("aikido_zen.background_process.cloud_connection_manager.on_start")
@patch(
    "aikido_zen.background_process.cloud_connection_manager.start_polling_for_changes"
)
@patch(
    "aikido_zen.background_process.cloud_connection_manager.send_heartbeats_every_x_secs"
)
@patch(
    "aikido_zen.background_process.cloud_connection_manager.listen_for_config_updates"
)
def test_start_enables_sse_when_server_flag_set(
    mock_listen_for_config_updates,
    mock_send_heartbeats,
    mock_start_polling,
    mock_on_start,
    setup_cloud_connection_manager,
):
    """SSE listening should start when the server enables the realtime_updates feature flag"""
    manager = setup_cloud_connection_manager
    mock_on_start.return_value = {"success": True}
    manager.conf.update_enabled_features(["realtime_updates"])

    manager.start(event_scheduler=MagicMock())

    mock_listen_for_config_updates.assert_called_once()


@patch("aikido_zen.background_process.cloud_connection_manager.on_start")
@patch(
    "aikido_zen.background_process.cloud_connection_manager.start_polling_for_changes"
)
@patch(
    "aikido_zen.background_process.cloud_connection_manager.send_heartbeats_every_x_secs"
)
@patch(
    "aikido_zen.background_process.cloud_connection_manager.listen_for_config_updates"
)
def test_start_does_not_enable_sse_without_flag(
    mock_listen_for_config_updates,
    mock_send_heartbeats,
    mock_start_polling,
    mock_on_start,
    setup_cloud_connection_manager,
):
    """SSE listening should not start when neither the env var nor the server flag is set"""
    manager = setup_cloud_connection_manager
    mock_on_start.return_value = {"success": True}

    manager.start(event_scheduler=MagicMock())

    mock_listen_for_config_updates.assert_not_called()


# Additional tests can be added here for other edge cases or scenarios
