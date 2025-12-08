"""Exports process_check_firewall_lists"""

from aikido_zen.helpers.ipc.command_types import Command, Payload, CommandContext


class CheckFirewallListsCommand(Command):

    @classmethod
    def identifier(cls) -> str:
        return "cfl"  # [C]heck [F]irewall [L]ists

    @classmethod
    def returns_data(cls) -> bool:
        return True

    @classmethod
    def run(cls, ctx: CommandContext, request):
        ip = request["ip"]
        if ip is not None and isinstance(ip, str):
            # Global IP Allowlist (e.g. for geofencing)
            if not ctx.connection_manager.firewall_lists.is_allowed_ip(ip):
                return {"blocked": True, "type": "allowlist"}

            # Global IP Blocklist (e.g. blocking known threat actors)
            reason = ctx.connection_manager.firewall_lists.is_blocked_ip(ip)
            if reason:
                return {
                    "blocked": True,
                    "type": "blocklist",
                    "reason": reason,
                }

        # User agent blocking (e.g. blocking AI scrapers)
        user_agent = request["user-agent"]
        if user_agent is not None and isinstance(user_agent, str):
            if ctx.connection_manager.firewall_lists.is_user_agent_blocked(user_agent):
                return {
                    "blocked": True,
                    "type": "bot-blocking",
                }

        return {"blocked": False}

    @classmethod
    def generate(cls, request) -> Payload:
        return Payload(cls, request)
