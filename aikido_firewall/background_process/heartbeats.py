"""
The code to send out a heartbeat is in here
"""

from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.create_interval import create_interval


def send_heartbeats_every_x_secs(reporter, interval_in_secs, event_scheduler):
    """
    Start sending out heartbeats every x seconds
    """
    if reporter.serverless:
        logger.debug("Running in serverless environment, not starting heartbeats")
        return
    if not reporter.token:
        logger.debug("No token provided, not starting heartbeats")
        return

    logger.debug("Starting heartbeats")

    # Create an interval for "interval_in_secs" seconds :
    create_interval(
        event_scheduler=event_scheduler,
        interval_in_secs=interval_in_secs,
        function=lambda reporter: reporter.send_heartbeat(),
        args=(reporter,),
    )
