"""
Exports update_blocked_ip_addresses
"""

from aikido_zen.helpers.logging import logger


def update_blocked_ip_addresses(connection_manager):
    """Will update service config with blocklist of IP addresses"""
    if not connection_manager.token or connection_manager.serverless:
        # Need token, and support in serverless mode is off for this feature
        return
    try:
        res = connection_manager.api.fetch_blocked_ips(connection_manager.token)
        if res.get("success") and res.get("blockedIPAddresses"):
            connection_manager.conf.set_blocked_ips(res.get("blockedIPAddresses"))
    except Exception as e:
        logger.debug("Exception in update_blocked_ip_addresses: %s", e)
