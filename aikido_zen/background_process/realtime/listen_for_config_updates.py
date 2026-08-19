"""
Mainly exports `listen_for_config_updates`
"""

import json
import time

from aikido_zen.helpers.token import Token
from aikido_zen.helpers.logging import logger
import aikido_zen.background_process.realtime as realtime
from .sse_client import connect_to_sse


def listen_for_config_updates(connection_manager, event_scheduler):
    """
    Connects to the realtime SSE endpoint and fetches the new config whenever
    the server signals, through a "config-updated" event, that it has changed.
    """
    if not isinstance(connection_manager.token, Token):
        logger.info("No token provided, not listening for config updates")
        return
    if connection_manager.serverless:
        logger.info(
            "Running in serverless environment, not listening for config updates"
        )
        return

    token = connection_manager.token
    last_updated_at = connection_manager.conf.last_updated_at
    last_config_refresh_started_at = None

    def config_update_arrived_too_fast():
        nonlocal last_config_refresh_started_at

        now = time.monotonic()
        if (
            last_config_refresh_started_at is not None
            and now - last_config_refresh_started_at
            < 9
        ):
            return True

        last_config_refresh_started_at = now
        return False

    def on_event(event):
        nonlocal last_updated_at

        logger.debug("SSE event received: %s", event.event)
        if event.event != "config-updated":
            return

        try:
            payload = json.loads(event.data)
            config_updated_at = payload["configUpdatedAt"]
            if config_updated_at <= last_updated_at:
                return
        except (ValueError, KeyError, TypeError):
            logger.debug("SSE config-updated event has invalid payload: %s", event.data)
            return

        if config_update_arrived_too_fast():
            logger.debug("SSE config-updated event ignored by refresh throttle")
            return

        logger.debug("SSE config-updated event, fetching new config")

        try:
            config = realtime.get_config(token)
            logger.debug(
                "SSE config fetched, configUpdatedAt: %s", config.get("configUpdatedAt")
            )
            last_updated_at = config.get("configUpdatedAt", config_updated_at)
        except Exception as e:
            logger.error("Failed to fetch config after SSE event : %s", e)
            return

        def apply_config():
            # Runs on the scheduler/reporting thread, so config updates stay
            # on a single writer thread
            connection_manager.update_service_config({**config, "success": True})
            connection_manager.update_firewall_lists()

        event_scheduler.enter(0, 1, apply_config)

    connect_to_sse(token=token, on_event=on_event)
