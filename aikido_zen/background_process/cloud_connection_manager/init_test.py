import weakref

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
import aikido_zen.test_utils as test_utils


@pytest.fixture
def setup_cloud_connection_manager():
    block = None  # Replace with appropriate mock or object if needed
    api = ReportingApiHTTP(None)  # Mock or create an instance of ReportingApiHTTP
    token = Token("AIK_TOKEN_TEST")  # Mock or create an instance of Token
    serverless = "some_value"  # Valid serverless value
    return CloudConnectionManager(block, api, token, serverless)


def test_report_api_event_only_adds_the_agent(setup_cloud_connection_manager):
    manager = setup_cloud_connection_manager
    manager.api.report = MagicMock(return_value={"success": True})

    manager.report_api_event({"type": "detected_attack", "time": 111})

    payload = manager.api.report.call_args[0][1]
    assert payload["time"] == 111
    assert "agent" in payload


def test_send_heartbeat_sets_the_time(setup_cloud_connection_manager):
    manager = setup_cloud_connection_manager
    manager.report_api_event = MagicMock(return_value={"success": True})

    with test_utils.patch_time(time_ms=111):
        manager.send_heartbeat()

    assert manager.report_api_event.call_args[0][0]["time"] == 111


def test_send_heartbeat_reports_and_clears_ai_stats(setup_cloud_connection_manager):
    manager = setup_cloud_connection_manager
    manager.report_api_event = MagicMock(return_value={"success": True})
    manager.ai_stats.on_ai_call("https://api.openai.com", "gpt-4o", 100, 20, 40, 0)
    manager.ai_stats.on_ai_tool_call("https://api.openai.com", "gpt-4o", "search")

    manager.send_heartbeat()

    heartbeat = manager.report_api_event.call_args[0][0]
    assert heartbeat["ai"] == [
        {
            "provider": "https://api.openai.com",
            "model": "gpt-4o",
            "calls": 1,
            "tokens": {
                "input": 100,
                "output": 20,
                "total": 120,
                "cacheRead": 40,
                "cacheWrite": 0,
            },
        }
    ]
    assert heartbeat["aiTools"] == [
        {
            "provider": "https://api.openai.com",
            "model": "gpt-4o",
            "name": "search",
            "calls": 1,
        }
    ]
    assert manager.ai_stats.empty() is True


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
@patch("aikido_zen.background_process.cloud_connection_manager.start_heartbeats")
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
@patch("aikido_zen.background_process.cloud_connection_manager.start_heartbeats")
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


@patch("aikido_zen.background_process.cloud_connection_manager.on_start")
@patch(
    "aikido_zen.background_process.cloud_connection_manager.start_polling_for_changes"
)
@patch("aikido_zen.background_process.cloud_connection_manager.start_heartbeats")
@patch(
    "aikido_zen.background_process.cloud_connection_manager.listen_for_config_updates"
)
def test_start_enables_sse_via_env_var(
    mock_listen_for_config_updates,
    mock_send_heartbeats,
    mock_start_polling,
    mock_on_start,
    setup_cloud_connection_manager,
    monkeypatch,
):
    """SSE listening should still start via the AIKIDO_FEATURE_SSE env var, without the server flag"""
    monkeypatch.setenv("AIKIDO_FEATURE_SSE", "true")
    manager = setup_cloud_connection_manager
    mock_on_start.return_value = {"success": True}

    manager.start(event_scheduler=MagicMock())

    mock_listen_for_config_updates.assert_called_once()


@patch("aikido_zen.background_process.cloud_connection_manager.on_start")
@patch(
    "aikido_zen.background_process.cloud_connection_manager.start_polling_for_changes"
)
@patch("aikido_zen.background_process.cloud_connection_manager.start_heartbeats")
@patch(
    "aikido_zen.background_process.cloud_connection_manager.listen_for_config_updates"
)
def test_start_does_not_enable_sse_for_unrelated_flag(
    mock_listen_for_config_updates,
    mock_send_heartbeats,
    mock_start_polling,
    mock_on_start,
    setup_cloud_connection_manager,
):
    """A server feature flag other than realtime_updates should not enable SSE"""
    manager = setup_cloud_connection_manager
    mock_on_start.return_value = {"success": True}
    manager.conf.update_enabled_features(["some_other_feature"])

    manager.start(event_scheduler=MagicMock())

    mock_listen_for_config_updates.assert_not_called()


@pytest.fixture
def reporting_manager(setup_cloud_connection_manager):
    manager = setup_cloud_connection_manager
    manager.api.report = MagicMock(return_value={"success": True})
    manager.max_attack_reports = 3
    manager.attack_report_window_ms = 10000
    return manager


def test_report_within_limit(reporting_manager):
    event = {"type": "detected_attack", "time": 1000}

    with test_utils.patch_time(time_s=2):
        response = reporting_manager.report_api_event(event)

    assert response == {"success": True}
    assert reporting_manager.attack_times == [1000]
    sent_event = reporting_manager.api.report.call_args[0][1]
    assert sent_event == {**event, "agent": sent_event["agent"]}
    reporting_manager.api.report.assert_called_once_with(
        reporting_manager.token, sent_event, reporting_manager.timeout_in_sec
    )


def test_report_exceeds_limit(reporting_manager):
    event = {"type": "detected_attack", "time": 1000}
    reporting_manager.attack_times = [1000, 2000, 3000]

    with test_utils.patch_time(time_s=4):
        response = reporting_manager.report_api_event(event)

    assert response == {"success": False, "error": "max_attacks_reached"}
    assert len(reporting_manager.attack_times) == 3
    reporting_manager.api.report.assert_not_called()


def test_report_within_limit_after_expiry(reporting_manager):
    reporting_manager.attack_times = [1000, 2001]
    event = {"type": "detected_attack", "time": 11000}

    with test_utils.patch_time(time_s=12):
        response = reporting_manager.report_api_event(event)

    assert response == {"success": True}
    assert len(reporting_manager.attack_times) == 2


def test_report_with_non_attack_event(reporting_manager):
    event = {"type": "other_event", "time": 1000}
    response = reporting_manager.report_api_event(event)

    assert response == {"success": True}
    assert len(reporting_manager.attack_times) == 0
    assert reporting_manager.api.report.call_args[0][1]["type"] == event["type"]


def test_report_multiple_events_within_limit(reporting_manager):
    events = [
        {"type": "detected_attack", "time": 1000},
        {"type": "detected_attack", "time": 2000},
        {"type": "detected_attack", "time": 3000},
    ]

    with test_utils.patch_time(time_s=4):
        for event in events:
            assert reporting_manager.report_api_event(event) == {"success": True}

    assert len(reporting_manager.attack_times) == 3
    assert reporting_manager.api.report.call_count == 3


def test_report_mixed_event_types(reporting_manager):
    attack_event = {"type": "detected_attack", "time": 1000}
    non_attack_event = {"type": "other_event", "time": 2000}

    assert reporting_manager.report_api_event(attack_event) == {"success": True}
    assert len(reporting_manager.attack_times) == 1
    assert reporting_manager.report_api_event(non_attack_event) == {"success": True}
    assert len(reporting_manager.attack_times) == 1


def test_report_event_expiry(reporting_manager):
    reporting_manager.attack_times = [1000, 1999]
    event = {"type": "detected_attack", "time": 11000}

    with test_utils.patch_time(time_s=12):
        response = reporting_manager.report_api_event(event)

    assert response == {"success": True}
    assert reporting_manager.attack_times == [11000]


def test_report_event_at_boundary(reporting_manager):
    reporting_manager.attack_times = [1999, 2000, 2001]
    event = {"type": "detected_attack", "time": 12000}

    with test_utils.patch_time(time_s=12):
        response = reporting_manager.report_api_event(event)

    assert response == {"success": True}
    assert reporting_manager.attack_times == [2001, 12000]


def test_report_does_not_retain_attack_payload(reporting_manager):
    class Request(dict):
        pass

    request = Request(body="attack")
    request_ref = weakref.ref(request)
    event = {"type": "detected_attack", "time": 1000, "request": request}

    with test_utils.patch_time(time_s=2):
        reporting_manager.report_api_event(event)

    assert reporting_manager.api.report.call_args[0][1]["request"] is request
    reporting_manager.api.report.reset_mock()
    del request, event
    assert request_ref() is None
