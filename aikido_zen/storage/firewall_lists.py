from aikido_zen.helpers.ip_matcher import IPMatcher
import regex as re

from aikido_zen.helpers.net.is_private_ip import is_private_ip


class FirewallLists:
    def __init__(self):
        self.blocked_ips = []
        self.allowed_ips = []
        self.monitored_ips = []
        self.blocked_user_agent_regex = None
        self.monitored_user_agent_regex = None
        self.user_agent_details = []

    def set_blocked_ips(self, blocked_ip_entries):
        self.blocked_ips = list(map(parse_ip_entry, blocked_ip_entries))

    def is_blocked_ip(self, ip):
        for entry in self.blocked_ips:
            if entry["iplist"].has(ip):
                return entry["description"]
        return False

    def get_matching_blocked_ip_list_keys(self, ip):
        return get_matching_ip_list_keys(self.blocked_ips, ip)

    def set_monitored_ips(self, monitored_ip_entries):
        self.monitored_ips = list(map(parse_ip_entry, monitored_ip_entries))

    def get_matching_monitored_ip_list_keys(self, ip):
        return get_matching_ip_list_keys(self.monitored_ips, ip)

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

    def set_monitored_user_agents(self, monitored_user_agents: str):
        if not monitored_user_agents:
            self.monitored_user_agent_regex = None
            return
        self.monitored_user_agent_regex = compile_pattern(monitored_user_agents)

    def is_monitored_user_agent(self, ua: str):
        if not ua:
            return False
        if not self.monitored_user_agent_regex:
            return False
        return self.monitored_user_agent_regex.search(ua)

    def set_user_agent_details(self, user_agent_details):
        self.user_agent_details = []
        for detail in user_agent_details:
            pattern = compile_pattern(detail["pattern"])
            if pattern:
                self.user_agent_details.append(
                    {"key": detail["key"], "pattern": pattern}
                )

    def get_matching_user_agent_keys(self, ua: str):
        return [
            detail["key"]
            for detail in self.user_agent_details
            if detail["pattern"].search(ua)
        ]


def compile_pattern(pattern):
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None


def get_matching_ip_list_keys(ip_lists, ip):
    return [entry["key"] for entry in ip_lists if entry["iplist"].has(ip)]


def parse_ip_entry(entry):
    """
    Converts ip entry: {"key": "geoip/nl", "source": "example", "description": "Example description", "ips": []}
    """
    return {
        "key": entry.get("key"),
        "source": entry["source"],
        "description": entry["description"],
        "iplist": IPMatcher(entry["ips"]),
    }
