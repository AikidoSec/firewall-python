"""Exports the send_heartbeat function"""

from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms


def send_heartbeat(connection_manager):
    """
    This will send a heartbeat to the server
    """
    if not connection_manager.token:
        return
    logger.debug("Aikido CloudConnectionManager : Sending out heartbeat")
    stats = connection_manager.statistics.get_stats()
    users = connection_manager.users.as_array()
    routes = list(connection_manager.routes)
    outgoing_domains = connection_manager.hostnames.as_array()

    connection_manager.statistics.reset()
    connection_manager.users.clear()
    connection_manager.routes.clear()
    connection_manager.hostnames.clear()
    res = connection_manager.api.report(
        connection_manager.token,
        {
            "type": "heartbeat",
            "time": get_unixtime_ms(),
            "agent": connection_manager.get_manager_info(),
            "stats": stats,
            "hostnames": outgoing_domains,
            "routes": routes,
            "users": users,
            "middlewareInstalled": connection_manager.middleware_installed,
        },
        connection_manager.timeout_in_sec,
    )
    connection_manager.update_service_config(res)
