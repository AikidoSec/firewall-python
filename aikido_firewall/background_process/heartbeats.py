"""
The code to send out a heartbeat is in here
"""

import sched, time
from aikido_firewall.helpers.logging import logger

# Create an event scheduler
s = sched.scheduler(time.time, time.sleep)


def send_heartbeats_every_x_secs(reporter, interval_in_secs):
    """
    Start sending out heartbeats every x seconds
    """
    if reporter.serverless:
        logger.debug("Running in serverless environment, not starting heartbeats")
        return
    if not reporter.token:
        logger.debug("No token provided, not starting heartbeats")

    # Interval already started code ?

    s.enter(0, 1, send_heartbeat_wrapper, (reporter, interval_in_secs))


def send_heartbeat_wrapper(rep, interval_in_secs):
    """
    Wrapper function for send_heartbeat so we get an interval
    """
    s.enter(interval_in_secs, 1, send_heartbeat_wrapper, (rep, interval_in_secs))
    logger.debug("Heartbeat...")
    rep.send_heartbeat()
