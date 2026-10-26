"""Exports process_check_firewall_lists"""


def process_check_firewall_lists(connection_manager, data):
    """
    Checks whether an IP is blocked, and counts the lists it matches for the heartbeat
    data: {"ip": string, "user-agent": string}
    returns -> {"blocked": boolean, "type": string, "reason": string}
    """
    firewall_lists = connection_manager.firewall_lists
    statistics = connection_manager.statistics

    ip = data["ip"]
    if ip is not None and isinstance(ip, str):
        # Global IP Allowlist (e.g. for geofencing)
        if not firewall_lists.is_allowed_ip(ip):
            return {"blocked": True, "type": "allowlist"}

        # Global IP Blocklist (e.g. blocking known threat actors)
        reason = firewall_lists.is_blocked_ip(ip)

        statistics.on_ip_address_matches(
            firewall_lists.get_matching_monitored_ip_list_keys(ip)
        )
        if reason:
            statistics.on_ip_address_matches(
                firewall_lists.get_matching_blocked_ip_list_keys(ip)
            )
            return {
                "blocked": True,
                "type": "blocklist",
                "reason": reason,
            }

    user_agent = data["user-agent"]
    if user_agent is not None and isinstance(user_agent, str):
        # User agent blocking (e.g. blocking AI scrapers)
        is_blocked = firewall_lists.is_user_agent_blocked(user_agent)

        if is_blocked or firewall_lists.is_monitored_user_agent(user_agent):
            statistics.on_user_agent_matches(
                firewall_lists.get_matching_user_agent_keys(user_agent)
            )
        if is_blocked:
            return {
                "blocked": True,
                "type": "bot-blocking",
            }

    return {
        "blocked": False,
    }
