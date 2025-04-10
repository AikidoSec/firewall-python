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

    connection_manager.conf.update(
        endpoints=res.get("endpoints", []),
        last_updated_at=res.get("configUpdatedAt", get_unixtime_ms()),
        blocked_uids=res.get("blockedUserIds", []),
        bypassed_ips=res.get("allowedIPAddresses", []),
        received_any_stats=res.get("receivedAnyStats", True),
    )
