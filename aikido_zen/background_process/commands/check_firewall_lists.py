from aikido_zen.helpers.ipc.command_types import Payload

IDENTIFIER = "CHECK_FIREWALL_LISTS"


def generate(ip, user_agent, timeout_in_sec=0.01) -> Payload:
    return Payload(IDENTIFIER, {"ip": ip, "user-agent": user_agent}, timeout_in_sec)


def process(connection_manager, request, queue):
    ip = request["ip"]
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

    user_agent = request["user-agent"]
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
