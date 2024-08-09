import pytest
from unittest.mock import MagicMock, patch
from aikido_firewall.helpers.token import Token
from .start_polling_for_changes import start_polling_for_changes, poll_for_changes


@pytest.fixture
def event_scheduler():
    class EventScheduler:
        def __init__(self):
            self.events = []

        def enter(self, delay, priority, action, argument):
            self.events.append((delay, priority, action, argument))

        def run(self):
            self.events[0][2](*self.events[0][3])

    return EventScheduler()


def test_no_token(event_scheduler, caplog):
    start_polling_for_changes(
        on_config_update=lambda config: pytest.fail("Should not be called"),
        serverless=None,
        token=None,
        event_scheduler=event_scheduler,
    )

    assert "No token provided, not polling for config updates" in caplog.text


def test_serverless_environment(event_scheduler, caplog):
    start_polling_for_changes(
        on_config_update=lambda config: pytest.fail("Should not be called"),
        serverless=True,
        token=Token("123"),
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
        "aikido_firewall.background_process.realtime.get_config_last_updated_at",
        side_effect=mock_get_config_last_updated_at,
    ), patch(
        "aikido_firewall.background_process.realtime.get_config",
        side_effect=mock_get_config,
    ):

        config_updates = []

        start_polling_for_changes(
            on_config_update=lambda config: config_updates.append(config),
            serverless=None,
            token=Token("123"),
            event_scheduler=event_scheduler,
        )

        # Run the event scheduler to simulate the polling
        event_scheduler.run()

        assert config_updates == []

        # Simulate a config update
        config_updated_at = 1
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
        "aikido_firewall.background_process.realtime.get_config_last_updated_at",
        side_effect=mock_get_config_last_updated_at,
    ):
        config_updates = []

        start_polling_for_changes(
            on_config_update=lambda config: config_updates.append(config),
            token=Token("123"),
            serverless=None,
            event_scheduler=event_scheduler,
        )

        # Run the event scheduler to simulate the polling
        event_scheduler.run()

        assert config_updates == []
        assert (
            "Failed to check for config updates due to error : Request timed out"
            in caplog.text
        )
