"""Exports the send_heartbeat function"""

from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.get_current_unixtime_ms import get_unixtime_ms


def send_heartbeat(reporter):
    """
    This will send a heartbeat to the server
    """
    if not reporter.token:
        return
    logger.debug("Aikido Reporter : Sending out heartbeat")
    users = reporter.users.as_array()
    routes = list(reporter.routes)
    outgoing_domains = reporter.hostnames.as_array()

    reporter.users.clear()
    reporter.routes.clear()
    reporter.hostnames.clear()
    res = reporter.api.report(
        reporter.token,
        {
            "type": "heartbeat",
            "time": get_unixtime_ms(),
            "agent": reporter.get_reporter_info(),
            "stats": {
                "sinks": {},
                "startedAt": 0,
                "endedAt": 0,
                "requests": {
                    "total": 0,
                    "aborted": 0,
                    "attacksDetected": {
                        "total": 0,
                        "blocked": 0,
                    },
                },
            },
            "hostnames": outgoing_domains,
            "routes": routes,
            "users": users,
        },
        reporter.timeout_in_sec,
    )
    reporter.update_service_config(res)
