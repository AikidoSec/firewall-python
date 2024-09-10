"""
The code to send out a heartbeat is in here
"""

from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.create_interval import create_interval


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

    # Create an interval for "interval_in_secs" seconds :
    create_interval(
        event_scheduler=event_scheduler,
        interval_in_secs=interval_in_secs,
        function=lambda connection_manager: connection_manager.send_heartbeat(),
        args=(connection_manager,),
    )
