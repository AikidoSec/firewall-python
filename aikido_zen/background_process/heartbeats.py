"""
The code to send out a heartbeat is in here
"""

from aikido_zen.helpers.logging import logger


def send_heartbeats_every_x_secs(connection_manager, interval_in_secs, event_scheduler):
    """
    Start sending out heartbeats every x seconds
    """
    if connection_manager.serverless:
        logger.debug("Running in serverless environment, not starting heartbeats")
        return
    if not connection_manager.token:
        logger.debug("No token provided, not starting heartbeats")
        return

    logger.debug("Starting heartbeats")

    def send_heartbeat():
        connection_manager.send_heartbeat()
        event_scheduler.enter(connection_manager.heartbeat_secs, 1, send_heartbeat)

    event_scheduler.enter(interval_in_secs, 1, send_heartbeat)
