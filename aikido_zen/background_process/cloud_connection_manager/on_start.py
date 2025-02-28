"""Mainly exports on_start function"""

from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms


def on_start(connection_manager):
    """
    This will send out an Event signalling the start to the server
    """
    if not connection_manager.token:
        return
    res = connection_manager.api.report(
        connection_manager.token,
        {
            "type": "started",
            "time": get_unixtime_ms(),
            "agent": connection_manager.get_manager_info(),
        },
        connection_manager.timeout_in_sec,
    )
    if not res.get("success", True):
        # Update config time even in failure :
        connection_manager.conf.last_updated_at = get_unixtime_ms()
        logger.error("Failed to communicate with Aikido Server : %s", res["error"])
    else:
        connection_manager.update_service_config(res)
        connection_manager.update_firewall_lists()
        logger.info("Established connection with Aikido Server")
    return res
