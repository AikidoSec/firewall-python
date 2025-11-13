"""Mainly exports update_service_config function"""

from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms


def update_service_config(connection_manager, res):
    """
    Update configuration based on the server's response
    """
    if res.get("success", False) is False:
        logger.debug(res)
        return
    if "block" in res.keys() and res["block"] != connection_manager.block:
        logger.debug("Updating blocking, setting blocking to : %s", res["block"])
        connection_manager.block = bool(res["block"])

    connection_manager.conf.set_endpoints(res.get("endpoints", []))
    connection_manager.conf.set_last_updated_at(
        res.get("configUpdatedAt", get_unixtime_ms())
    )
    connection_manager.conf.set_blocked_user_ids(res.get("blockedUserIds", []))
    connection_manager.conf.set_bypassed_ips(res.get("allowedIPAddresses", []))
    if res.get("receivedAnyStats", True):
        connection_manager.conf.enable_received_stats()
