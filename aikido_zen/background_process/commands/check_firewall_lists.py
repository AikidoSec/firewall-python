"""Exports process_check_firewall_lists"""


def process_check_firewall_lists(connection_manager, data):
    """
    Checks whether an IP is blocked and whether there is an ongoing attack wave
    data: {"ip": string, "user-agent": string}
    returns -> CheckFirewallListsRes
    """
    ip = data["ip"]
    if ip is not None and isinstance(ip, str):
        # Global IP Allowlist (e.g. for geofencing)
        if not connection_manager.firewall_lists.is_allowed_ip(ip):
            return CheckFirewallListsRes(blocked=True, blocking_type="allowlist")

        # Global IP Blocklist (e.g. blocking known threat actors)
        reason = connection_manager.firewall_lists.is_blocked_ip(ip)
        if reason:
            return CheckFirewallListsRes(
                blocked=True, blocking_type="blocklist", reason=reason
            )

    user_agent = data["user-agent"]
    if user_agent is not None and isinstance(user_agent, str):
        # User agent blocking (e.g. blocking AI scrapers)
        if connection_manager.firewall_lists.is_user_agent_blocked(user_agent):
            return CheckFirewallListsRes(blocked=True, blocking_type="bot-blocking")

    return CheckFirewallListsRes()


class CheckFirewallListsRes:
    def __init__(self, blocked=False, blocking_type=None, reason=None):
        self.blocked = blocked
        self.blocking_type = blocking_type
        self.reason = reason
