"""
Exports update_firewall_lists
"""

from aikido_zen.helpers.logging import logger


def update_firewall_lists(connection_manager):
    """Will update service config with blocklist of IP addresses"""
    if not connection_manager.token or connection_manager.serverless:
        # Need token, and support in serverless mode is off for this feature
        return
    try:
        res = connection_manager.api.fetch_firewall_lists(connection_manager.token)
        if not res.get("success"):
            return
        if res.get("blockedIPAddresses"):
            connection_manager.conf.set_blocked_ips(res.get("blockedIPAddresses"))
        if res.get("allowedIPAddresses"):
            connection_manager.conf.set_allowed_ips(res.get("allowedIPAddresses"))
        if res.get("blockedUserAgents"):
            connection_manager.conf.set_blocked_user_agents(
                res.get("blockedUserAgents")
            )

    except Exception as e:
        logger.debug("Exception in update_firewall_lists: %s", e)
