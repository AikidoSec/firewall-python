"""
The code to send out a heartbeat is in here
"""

from aikido_zen.helpers.logging import logger


def start_heartbeats(connection_manager, event_scheduler):
    if connection_manager.serverless:
        logger.debug("Running in serverless environment, not starting heartbeats")
        return
    if not connection_manager.token:
        logger.debug("No token provided, not starting heartbeats")
        return

    logger.debug("Starting heartbeats")

    def send_heartbeat(initial=False):
        connection_manager.send_heartbeat()
        next_interval_in_secs = 120 if initial else connection_manager.heartbeat_secs
        event_scheduler.enter(next_interval_in_secs, 1, send_heartbeat)

    event_scheduler.enter(30, 1, send_heartbeat, (True,))
