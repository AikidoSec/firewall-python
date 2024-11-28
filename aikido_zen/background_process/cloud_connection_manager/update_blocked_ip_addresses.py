"""
Exports update_blocked_ip_addresses
"""

from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from aikido_zen.sinks.pymysql import logger


def update_blocked_ip_addresses(ccm: CloudConnectionManager):
    """Will update service config with blocklist of IP addresses"""
    if not ccm.token or ccm.serverless:
        # Need token, and support in serverless mode is off for this feature
        return
    try:
        pass
        blocked_ips = fetch()
        ccm.conf.blocked_ips = blocked_ips
    except Exception as e:
        logger.debug("Exception in update_blocked_ip_addresses: %s", e)
