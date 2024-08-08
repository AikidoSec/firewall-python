"""Mainly exports on_start function"""

from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.get_current_unixtime_ms import get_unixtime_ms


def on_start(reporter):
    """
    This will send out an Event signalling the start to the server
    """
    if not reporter.token:
        return
    res = reporter.api.report(
        reporter.token,
        {
            "type": "started",
            "time": get_unixtime_ms(),
            "agent": reporter.get_reporter_info(),
        },
        reporter.timeout_in_sec,
    )
    if not res.get("success", True):
        logger.error("Failed to communicate with Aikido Server : %s", res["error"])
    else:
        reporter.update_service_config(res)
        logger.info("Established connection with Aikido Server")
