import pytest
from unittest.mock import MagicMock, patch
from aikido_zen.helpers.token import Token
from .start_polling_for_changes import start_polling_for_changes, poll_for_changes


@pytest.fixture
def event_scheduler():
    class EventScheduler:
        def __init__(self):
            self.events = []

        def enter(self, delay, priority, action, argument):
            self.events.append((delay, priority, action, argument))

        def run(self):
            if self.events:
                self.events[0][2](*self.events[0][3])

    return EventScheduler()


def test_no_token(event_scheduler, caplog):
    start_polling_for_changes(
        connection_manager=MagicMock(token=None, serverless=None),
        event_scheduler=event_scheduler,
    )

    assert "No token provided, not polling for config updates" in caplog.text


def test_serverless_environment(event_scheduler, caplog):
    start_polling_for_changes(
        connection_manager=MagicMock(token=Token("123"), serverless=True),
        event_scheduler=event_scheduler,
    )

    assert (
        "Running in serverless environment, not polling for config updates"
        in caplog.text
    )


def test_check_for_config_updates(event_scheduler):
    calls = []
    config_updated_at = 0

    def mock_get_config_last_updated_at(token):
        return config_updated_at

    def mock_get_config(token):
        return {"endpoints": [], "heartbeatIntervalInMS": 600000}

    with patch(
        "aikido_zen.background_process.realtime.get_config_last_updated_at",
        side_effect=mock_get_config_last_updated_at,
    ), patch(
        "aikido_zen.background_process.realtime.get_config",
        side_effect=mock_get_config,
    ):
        config_updates = []

        connection_manager = MagicMock(
            update_service_config=lambda config: config_updates.append(config),
            token=Token("123"),
            conf=MagicMock(last_updated_at=config_updated_at),
            serverless=None,
        )

        start_polling_for_changes(
            connection_manager=connection_manager,
            event_scheduler=event_scheduler,
        )

        # Run the event scheduler to simulate the polling
        event_scheduler.run()

        assert config_updates == []

        # Simulate a config update
        config_updated_at = 1
        connection_manager.conf.last_updated_at = config_updated_at
        event_scheduler.run()

        assert config_updates == [
            {
                "endpoints": [],
                "heartbeatIntervalInMS": 600000,
                "success": True,
            },
        ]


def test_api_error_handling(event_scheduler, caplog):
    def mock_get_config_last_updated_at(token):
        raise ValueError("Request timed out")

    with patch(
        "aikido_zen.background_process.realtime.get_config_last_updated_at",
        side_effect=mock_get_config_last_updated_at,
    ):
        config_updates = []

        connection_manager = MagicMock(
            update_service_config=lambda config: config_updates.append(config),
            token=Token("123"),
            conf=MagicMock(last_updated_at=0),
            serverless=None,
        )

        start_polling_for_changes(
            connection_manager=connection_manager,
            event_scheduler=event_scheduler,
        )

        # Run the event scheduler to simulate the polling
        event_scheduler.run()

        assert config_updates == []
        assert (
            "Failed to check for config updates due to error : Request timed out"
            in caplog.text
        )
