"""
The code to send out a heartbeat is in here
"""

from aikido_firewall.helpers.logging import logger


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

    event_scheduler.enter(
        0, 1, send_heartbeat_wrapper, (reporter, interval_in_secs, event_scheduler)
    )


def send_heartbeat_wrapper(rep, interval_in_secs, event_scheduler):
    """
    Wrapper function for send_heartbeat so we get an interval
    """
    event_scheduler.enter(
        interval_in_secs,
        1,
        send_heartbeat_wrapper,
        (rep, interval_in_secs, event_scheduler),
    )
    logger.debug("Heartbeat...")
    rep.send_heartbeat()
