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

    # Start the interval by booting the first settimeout
    send_heartbeat_wrapper(reporter, interval_in_secs, event_scheduler, True)


def send_heartbeat_wrapper(rep, interval_in_secs, event_scheduler, boot=False):
    """
    Wrapper function for send_heartbeat so we get an interval
    """
    event_scheduler.enter(
        interval_in_secs,
        1,
        send_heartbeat_wrapper,
        (rep, interval_in_secs, event_scheduler),
    )
    if not boot:
        #  If boot is true it means it's the first time this gets executed, so we
        #  need to wait for the interval in the event scheduler to finish
        logger.debug("Heartbeat...")
        rep.send_heartbeat()
