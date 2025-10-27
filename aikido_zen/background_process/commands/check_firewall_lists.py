"""Exports process_check_firewall_lists"""

from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from aikido_zen.background_process.packages import PackagesStore
from aikido_zen.helpers.logging import logger


def process_check_firewall_lists(
    connection_manager: CloudConnectionManager, data, conn, queue=None
):
    """
    Checks whether an IP is blocked
    data: {"ip": string, "user-agent": string}
    returns -> {"blocked": boolean, "type": string, "reason": string}
    """
    ip = data["ip"]
    if ip is not None and isinstance(ip, str):
        # Global IP Allowlist (e.g. for geofencing)
        if not connection_manager.firewall_lists.is_allowed_ip(ip):
            return {"blocked": True, "type": "allowlist"}

        # Global IP Blocklist (e.g. blocking known threat actors)
        reason = connection_manager.firewall_lists.is_blocked_ip(ip)
        if reason:
            return {
                "blocked": True,
                "type": "blocklist",
                "reason": reason,
            }

    user_agent = data["user-agent"]
    if user_agent is not None and isinstance(user_agent, str):
        # User agent blocking (e.g. blocking AI scrapers)
        if connection_manager.firewall_lists.is_user_agent_blocked(user_agent):
            return {
                "blocked": True,
                "type": "bot-blocking",
            }

    return {
        "blocked": False,
    }
