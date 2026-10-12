import pytest
import sched
from unittest.mock import Mock, patch
from aikido_zen.background_process.heartbeats import start_heartbeats
from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)


def test_send_heartbeats_serverless():
    connection_manager = Mock()
    connection_manager.serverless = True
    connection_manager.token = "mocked_token"
    event_scheduler = Mock()

    with patch("aikido_zen.helpers.logging.logger.debug") as mock_debug:
        start_heartbeats(connection_manager, event_scheduler)

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
        start_heartbeats(connection_manager, event_scheduler)

    mock_debug.assert_called_once_with("No token provided, not starting heartbeats")
    event_scheduler.enter.assert_not_called()


@pytest.fixture
def heartbeat_schedule():
    now = [0]
    scheduler = sched.scheduler(lambda: now[0], lambda _: None)
    manager = CloudConnectionManager(False, Mock(), "mocked_token", None)
    manager.send_heartbeat = Mock()

    def start():
        start_heartbeats(manager, scheduler)

    def advance_to(seconds):
        while scheduler.queue[0].time <= seconds:
            now[0] = scheduler.queue[0].time
            scheduler.run(blocking=False)
        now[0] = seconds

    return manager, start, advance_to


def test_default_heartbeat_interval(heartbeat_schedule):
    manager, start, advance_to = heartbeat_schedule
    start()
    advance_to(29)
    manager.send_heartbeat.assert_not_called()
    advance_to(30)
    manager.send_heartbeat.assert_called_once()
    advance_to(149)
    manager.send_heartbeat.assert_called_once()
    advance_to(150)
    assert manager.send_heartbeat.call_count == 2
    advance_to(749)
    assert manager.send_heartbeat.call_count == 2
    advance_to(750)
    assert manager.send_heartbeat.call_count == 3
    advance_to(1350)
    assert manager.send_heartbeat.call_count == 4


@pytest.mark.parametrize("failed_report", [0, 1, 2])
def test_heartbeat_exception_does_not_stop_schedule(
    heartbeat_schedule, failed_report, caplog
):
    manager, start, advance_to = heartbeat_schedule
    responses = [None] * 4
    responses[failed_report] = RuntimeError("heartbeat failed")
    manager.send_heartbeat.side_effect = responses

    start()
    advance_to(1350)

    assert manager.send_heartbeat.call_count == 4
    assert "Failed to send heartbeat: heartbeat failed" in caplog.text


def test_interval_updates_apply_when_scheduling_next_heartbeat(heartbeat_schedule):
    manager, start, advance_to = heartbeat_schedule
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": 120_000})
    start()
    advance_to(30)
    manager.send_heartbeat.assert_called_once()
    advance_to(60)
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": 300_000})
    advance_to(150)
    assert manager.send_heartbeat.call_count == 2

    advance_to(449)
    assert manager.send_heartbeat.call_count == 2
    advance_to(450)
    assert manager.send_heartbeat.call_count == 3
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": 120_000})
    advance_to(750)
    assert manager.send_heartbeat.call_count == 4
    advance_to(870)
    assert manager.send_heartbeat.call_count == 5


@pytest.mark.parametrize("value", [None, 0, -1, 30_000, 59_999, "60000", True])
def test_invalid_interval_keeps_previous_value(heartbeat_schedule, value):
    manager, start, advance_to = heartbeat_schedule
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": value})
    assert manager.heartbeat_secs == 600
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": 120_000})
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": value})
    start()
    advance_to(269)
    assert manager.send_heartbeat.call_count == 2
    advance_to(270)
    assert manager.send_heartbeat.call_count == 3


def test_failed_response_does_not_change_interval(heartbeat_schedule):
    manager, start, advance_to = heartbeat_schedule
    manager.update_service_config({"success": False, "heartbeatIntervalInMS": 120_000})
    start()
    advance_to(749)
    assert manager.send_heartbeat.call_count == 2
    advance_to(750)
    assert manager.send_heartbeat.call_count == 3
    assert manager.heartbeat_secs == 600


@pytest.mark.parametrize("interval", [60, 120, 600])
@pytest.mark.parametrize("received_any_stats", [False, True])
@pytest.mark.parametrize("serverless", [None, "aws_lambda"])
def test_startup_schedule_sends_two_early_reports_then_uses_configured_interval(
    interval, received_any_stats, serverless
):
    now = [0]
    scheduler = sched.scheduler(lambda: now[0], lambda _: None)
    api = Mock()
    api.report.return_value = {
        "success": True,
        "receivedAnyStats": received_any_stats,
        "heartbeatIntervalInMS": interval * 1000,
    }
    manager = CloudConnectionManager(False, api, "mocked_token", serverless)
    manager.update_firewall_lists = Mock()
    manager.send_heartbeat = Mock()
    with patch(
        "aikido_zen.background_process.cloud_connection_manager.start_polling_for_changes"
    ):
        manager.start(scheduler)
    reports_enabled = int(not serverless)
    assert len(scheduler.queue) == reports_enabled
    for seconds, expected_reports in (
        (29, 0),
        (30, reports_enabled),
        (149, reports_enabled),
        (150, 2 * reports_enabled),
        (150 + interval - 1, 2 * reports_enabled),
        (150 + interval, 3 * reports_enabled),
        (150 + 2 * interval, 4 * reports_enabled),
    ):
        now[0] = seconds
        scheduler.run(blocking=False)
        assert manager.send_heartbeat.call_count == expected_reports
    assert len(scheduler.queue) == reports_enabled
