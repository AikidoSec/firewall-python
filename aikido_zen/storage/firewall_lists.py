from aikido_zen.helpers.ip_matcher import IPMatcher
import regex as re

from aikido_zen.vulnerabilities.ssrf.is_private_ip import is_private_ip


class FirewallLists:
    def __init__(self):
        self.blocked_ips = []
        self.allowed_ips = []
        self.blocked_user_agent_regex = None

    def set_blocked_ips(self, blocked_ip_entries):
        self.blocked_ips = list(map(parse_ip_entry, blocked_ip_entries))

    def is_blocked_ip(self, ip):
        for entry in self.blocked_ips:
            if entry["iplist"].has(ip):
                return entry["description"]
        return False

    def set_allowed_ips(self, allowed_ip_entries):
        self.allowed_ips = list(map(parse_ip_entry, allowed_ip_entries))

    def is_allowed_ip(self, ip):
        # If allowed_ips is empty, we are not in allow mode, so we don't check
        if len(self.allowed_ips) == 0:
            return True
        # We don't want to block local ip addresses
        if is_private_ip(ip):
            return True

        for entry in self.allowed_ips:
            if entry["iplist"].has(ip):
                # The ip only needs to match with one of the lists, not all.
                return True

        return False

    def set_blocked_user_agents(self, blocked_user_agents: str):
        if not blocked_user_agents:
            self.blocked_user_agent_regex = None
            return
        self.blocked_user_agent_regex = re.compile(blocked_user_agents, re.IGNORECASE)

    def is_user_agent_blocked(self, ua: str):
        if not ua:
            return False
        if not self.blocked_user_agent_regex:
            return False
        return self.blocked_user_agent_regex.search(ua)


def parse_ip_entry(entry):
    """
    Converts ip entry: {"source": "example", "description": "Example description", "ips": []}
    """
    return {
        "source": entry["source"],
        "description": entry["description"],
        "iplist": IPMatcher(entry["ips"]),
    }
