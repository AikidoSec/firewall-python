"""
Exports update_firewall_lists
"""

from aikido_zen.background_process.api.helpers import Response
from aikido_zen.helpers.logging import logger


def update_firewall_lists(connection_manager):
    """Fetches firewall lists from core and updates config (blocked/allowed IPs, blocked user agents)"""
    if not connection_manager.token or connection_manager.serverless:
        # We need a token, and support in serverless mode is off for this feature
        return
    try:
        res: Response = connection_manager.api.fetch_firewall_lists(
            connection_manager.token
        )
        if not res.success:
            # Something went wong getting lists from API
            return

        blocked_ips = res.json.get("blockedIPAddresses")
        allowed_ips = res.json.get("allowedIPAddresses")
        blocked_user_agents = res.json.get("blockedUserAgents")

        # Validate response
        if not isinstance(blocked_ips, list) or not isinstance(allowed_ips, list):
            return
        if not isinstance(blocked_user_agents, str):
            return

        connection_manager.firewall_lists.set_blocked_ips(blocked_ips)
        connection_manager.firewall_lists.set_allowed_ips(allowed_ips)
        connection_manager.firewall_lists.set_blocked_user_agents(blocked_user_agents)

    except Exception as e:
        logger.debug("Exception in update_firewall_lists: %s", e)
