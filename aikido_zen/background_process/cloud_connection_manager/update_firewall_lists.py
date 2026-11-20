"""
Exports update_firewall_lists
"""

from aikido_zen.helpers.logging import logger


def update_firewall_lists(connection_manager):
    """Fetches firewall lists from core and updates config (blocked/allowed IPs, blocked user agents)"""
    if not connection_manager.token or connection_manager.serverless:
        # We need a token, and support in serverless mode is off for this feature
        return
    try:
        res = connection_manager.api.fetch_firewall_lists(connection_manager.token)
        blocked_ips = res.get("blockedIPAddresses")
        allowed_ips = res.get("allowedIPAddresses")
        blocked_user_agents = res.get("blockedUserAgents")
        # Only used for heartbeat stats, so these may be missing.
        monitored_ips = res.get("monitoredIPAddresses") or []
        monitored_user_agents = res.get("monitoredUserAgents")
        user_agent_details = res.get("userAgentDetails") or []

        # Validate response
        if not res.get("success"):
            return
        if not isinstance(blocked_ips, list) or not isinstance(allowed_ips, list):
            return
        if not isinstance(blocked_user_agents, str):
            return

        connection_manager.firewall_lists.update(
            blocked_ips,
            allowed_ips,
            blocked_user_agents,
            monitored_ips,
            monitored_user_agents,
            user_agent_details,
        )

    except Exception as e:
        logger.debug("Exception in update_firewall_lists: %s", e)
