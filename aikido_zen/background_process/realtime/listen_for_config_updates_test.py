import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from aikido_zen.helpers.token import Token
from .listen_for_config_updates import listen_for_config_updates


def make_event(event="config-updated", data=None):
    return SimpleNamespace(
        event=event, data=json.dumps(data) if data is not None else ""
    )


@pytest.fixture
def connection_manager():
    return MagicMock(
        token=Token("123"),
        serverless=None,
        conf=MagicMock(last_updated_at=0),
    )


def test_no_token(caplog):
    with patch(
        "aikido_zen.background_process.realtime.listen_for_config_updates.connect_to_sse"
    ) as mock_connect:
        listen_for_config_updates(
            connection_manager=MagicMock(token=None, serverless=None),
            event_scheduler=MagicMock(),
        )

    assert "No token provided, not listening for config updates" in caplog.text
    mock_connect.assert_not_called()


def test_serverless_environment(caplog):
    with patch(
        "aikido_zen.background_process.realtime.listen_for_config_updates.connect_to_sse"
    ) as mock_connect:
        listen_for_config_updates(
            connection_manager=MagicMock(token=Token("123"), serverless=True),
            event_scheduler=MagicMock(),
        )

    assert (
        "Running in serverless environment, not listening for config updates"
        in caplog.text
    )
    mock_connect.assert_not_called()


def test_connects_to_sse_with_token(connection_manager):
    with patch(
        "aikido_zen.background_process.realtime.listen_for_config_updates.connect_to_sse"
    ) as mock_connect:
        listen_for_config_updates(
            connection_manager=connection_manager, event_scheduler=MagicMock()
        )

    mock_connect.assert_called_once()
    assert mock_connect.call_args.kwargs["token"] is connection_manager.token
    assert callable(mock_connect.call_args.kwargs["on_event"])


def get_on_event(connection_manager, event_scheduler=None):
    if event_scheduler is None:
        event_scheduler = MagicMock()
    with patch(
        "aikido_zen.background_process.realtime.listen_for_config_updates.connect_to_sse"
    ) as mock_connect:
        listen_for_config_updates(
            connection_manager=connection_manager, event_scheduler=event_scheduler
        )
    return mock_connect.call_args.kwargs["on_event"]


def make_inline_scheduler():
    scheduler = MagicMock()
    scheduler.enter.side_effect = lambda delay, priority, action, argument=(): action(
        *argument
    )
    return scheduler


def test_ignores_events_that_are_not_config_updated(connection_manager):
    on_event = get_on_event(connection_manager)

    with patch("aikido_zen.background_process.realtime.get_config") as mock_get_config:
        on_event(make_event(event="ping"))

    mock_get_config.assert_not_called()
    connection_manager.update_service_config.assert_not_called()


def test_ignores_config_updated_event_with_invalid_json(connection_manager, caplog):
    caplog.set_level(logging.DEBUG, logger="Zen")
    on_event = get_on_event(connection_manager)

    with patch("aikido_zen.background_process.realtime.get_config") as mock_get_config:
        on_event(SimpleNamespace(event="config-updated", data="not json"))

    mock_get_config.assert_not_called()
    connection_manager.update_service_config.assert_not_called()
    assert "SSE config-updated event has invalid payload" in caplog.text


def test_ignores_config_updated_event_missing_config_updated_at(connection_manager):
    on_event = get_on_event(connection_manager)

    with patch("aikido_zen.background_process.realtime.get_config") as mock_get_config:
        on_event(make_event(data={"foo": "bar"}))

    mock_get_config.assert_not_called()
    connection_manager.update_service_config.assert_not_called()


def test_ignores_config_updated_event_that_is_not_newer(connection_manager):
    connection_manager.conf.last_updated_at = 100
    on_event = get_on_event(connection_manager)

    with patch("aikido_zen.background_process.realtime.get_config") as mock_get_config:
        on_event(make_event(data={"configUpdatedAt": 100}))

    mock_get_config.assert_not_called()
    connection_manager.update_service_config.assert_not_called()


def test_fetches_and_applies_new_config_on_newer_event(connection_manager):
    connection_manager.conf.last_updated_at = 100
    event_scheduler = make_inline_scheduler()
    on_event = get_on_event(connection_manager, event_scheduler)

    new_config = {"endpoints": [], "configUpdatedAt": 200}
    with patch(
        "aikido_zen.background_process.realtime.get_config", return_value=new_config
    ) as mock_get_config:
        on_event(make_event(data={"configUpdatedAt": 200}))

    mock_get_config.assert_called_once_with(connection_manager.token)
    connection_manager.update_service_config.assert_called_once_with(
        {**new_config, "success": True}
    )
    connection_manager.update_firewall_lists.assert_called_once()


def test_applying_the_new_config_is_scheduled_on_the_event_scheduler(
    connection_manager,
):
    connection_manager.conf.last_updated_at = 100
    event_scheduler = MagicMock()
    on_event = get_on_event(connection_manager, event_scheduler)

    new_config = {"endpoints": [], "configUpdatedAt": 200}
    with patch(
        "aikido_zen.background_process.realtime.get_config", return_value=new_config
    ):
        on_event(make_event(data={"configUpdatedAt": 200}))

    connection_manager.update_service_config.assert_not_called()
    connection_manager.update_firewall_lists.assert_not_called()
    event_scheduler.enter.assert_called_once()
    args, _kwargs = event_scheduler.enter.call_args
    assert args[0] == 0  # run as soon as possible
    assert callable(args[2])


def test_updates_last_updated_at_so_a_second_stale_event_is_ignored(
    connection_manager,
):
    connection_manager.conf.last_updated_at = 100
    event_scheduler = make_inline_scheduler()
    on_event = get_on_event(connection_manager, event_scheduler)

    new_config = {"endpoints": [], "configUpdatedAt": 200}
    with patch(
        "aikido_zen.background_process.realtime.get_config", return_value=new_config
    ) as mock_get_config:
        on_event(make_event(data={"configUpdatedAt": 200}))
        # A second event claiming to be newer than the original lastUpdatedAt
        # (100), but not newer than what we just fetched (200), should now be
        # ignored without fetching again.
        on_event(make_event(data={"configUpdatedAt": 150}))

    mock_get_config.assert_called_once()


def test_handles_get_config_failure_gracefully(connection_manager, caplog):
    connection_manager.conf.last_updated_at = 100
    on_event = get_on_event(connection_manager)

    with patch(
        "aikido_zen.background_process.realtime.get_config",
        side_effect=ValueError("Request timed out"),
    ):
        on_event(make_event(data={"configUpdatedAt": 200}))

    connection_manager.update_service_config.assert_not_called()
    assert "Failed to fetch config after SSE event" in caplog.text
