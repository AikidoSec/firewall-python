"""Mainly exports on_start function"""

from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms


def on_start(connection_manager):
    event = {"type": "started"}
    res = connection_manager.report_api_event(event)

    if not res.get("success", True):
        connection_manager.conf.last_updated_at = (
            get_unixtime_ms()
        )  # Update config time even in failure
    else:
        connection_manager.update_service_config(res)
        connection_manager.update_firewall_lists()
        logger.info("Established connection with Aikido Server")

    return res
