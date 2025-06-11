"""Exports the send_heartbeat function"""

from aikido_zen.background_process.packages import PackagesStore
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms


def send_heartbeat(connection_manager):
    """
    This will send a heartbeat to the server
    """
    if not connection_manager.token:
        return
    logger.debug("Aikido CloudConnectionManager : Sending out heartbeat")
    stats = connection_manager.statistics.get_record()
    users = connection_manager.users.as_array()
    routes = list(connection_manager.routes)
    outgoing_domains = connection_manager.hostnames.as_array()
    ai_stats = connection_manager.ai_stats.get_stats()
    packages = PackagesStore.export()

    connection_manager.statistics.clear()
    connection_manager.users.clear()
    connection_manager.routes.clear()
    connection_manager.hostnames.clear()
    connection_manager.ai_stats.clear()
    PackagesStore.clear()

    res = connection_manager.api.report(
        connection_manager.token,
        {
            "type": "heartbeat",
            "time": get_unixtime_ms(),
            "agent": connection_manager.get_manager_info(),
            "stats": stats,
            "ai": ai_stats,
            "hostnames": outgoing_domains,
            "packages": packages,
            "routes": routes,
            "users": users,
            "middlewareInstalled": connection_manager.middleware_installed,
        },
        connection_manager.timeout_in_sec,
    )
    connection_manager.update_service_config(res)
