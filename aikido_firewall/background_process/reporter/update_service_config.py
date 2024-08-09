"""Mainly exports update_service_config function"""

from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.get_current_unixtime_ms import get_unixtime_ms
from ..service_config import ServiceConfig


def update_service_config(reporter, res):
    """
    Update configuration based on the server's response
    """
    if res["success"] is False:
        logger.debug(res)
        return
    if "block" in res.keys() and res["block"] != reporter.block:
        logger.debug("Updating blocking, setting blocking to : %s", res["block"])
        reporter.block = bool(res["block"])

    if res["endpoints"]:
        if not isinstance(res["endpoints"], list):
            res["endpoints"] = []  # Empty list
        reporter.conf = ServiceConfig(
            endpoints=res["endpoints"],
            last_updated_at=get_unixtime_ms(),
            blocked_uids=res["blockedUserIds"],
            bypassed_ips=res["allowedIPAddresses"],
        )
