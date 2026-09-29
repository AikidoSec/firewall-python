import pytest
import sched
from unittest.mock import Mock, patch
from aikido_zen.background_process.heartbeats import send_heartbeats_every_x_secs
from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)


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


@pytest.fixture
def heartbeat_schedule():
    now = [0]
    scheduler = sched.scheduler(lambda: now[0], lambda _: None)
    manager = CloudConnectionManager(False, Mock(), "mocked_token", None)
    manager.send_heartbeat = Mock()

    def start():
        send_heartbeats_every_x_secs(manager, manager.heartbeat_secs, scheduler)

    def advance_to(seconds):
        while scheduler.queue[0].time <= seconds:
            now[0] = scheduler.queue[0].time
            scheduler.run(blocking=False)
        now[0] = seconds

    return manager, start, advance_to


def test_default_heartbeat_interval(heartbeat_schedule):
    manager, start, advance_to = heartbeat_schedule
    start()
    advance_to(599)
    manager.send_heartbeat.assert_not_called()
    advance_to(600)
    manager.send_heartbeat.assert_called_once()
    advance_to(1200)
    assert manager.send_heartbeat.call_count == 2


def test_interval_updates_apply_when_scheduling_next_heartbeat(heartbeat_schedule):
    manager, start, advance_to = heartbeat_schedule
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": 120_000})
    start()
    advance_to(119)
    manager.send_heartbeat.assert_not_called()
    advance_to(120)
    manager.send_heartbeat.assert_called_once()
    advance_to(150)
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": 300_000})
    advance_to(240)
    assert manager.send_heartbeat.call_count == 2

    advance_to(539)
    assert manager.send_heartbeat.call_count == 2
    advance_to(540)
    assert manager.send_heartbeat.call_count == 3


@pytest.mark.parametrize("value", [None, 0, -1, 60_000, 119_999, "120000", True])
def test_invalid_interval_keeps_previous_value(heartbeat_schedule, value):
    manager, start, advance_to = heartbeat_schedule
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": value})
    assert manager.heartbeat_secs == 600
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": 120_000})
    manager.update_service_config({"success": True, "heartbeatIntervalInMS": value})
    start()
    advance_to(120)
    manager.send_heartbeat.assert_called_once()


def test_failed_response_does_not_change_interval(heartbeat_schedule):
    manager, start, advance_to = heartbeat_schedule
    manager.update_service_config({"success": False, "heartbeatIntervalInMS": 120_000})
    start()
    advance_to(120)
    manager.send_heartbeat.assert_not_called()
    assert manager.heartbeat_secs == 600


def test_startup_response_sets_interval_and_keeps_initial_stats():
    now = [0]
    scheduler = sched.scheduler(lambda: now[0], lambda _: None)
    api = Mock()
    api.report.return_value = {
        "success": True,
        "receivedAnyStats": False,
        "heartbeatIntervalInMS": 120_000,
    }
    manager = CloudConnectionManager(False, api, "mocked_token", None)
    manager.update_firewall_lists = Mock()
    manager.send_heartbeat = Mock()
    manager.statistics.empty = Mock(return_value=False)
    with patch(
        "aikido_zen.background_process.cloud_connection_manager.start_polling_for_changes"
    ):
        manager.start(scheduler)
    for seconds in (30, 60, 90, 120):
        now[0] = seconds
        scheduler.run(blocking=False)
        assert manager.send_heartbeat.call_count == (seconds >= 60) + (seconds >= 120)
