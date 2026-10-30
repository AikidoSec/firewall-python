from aikido_zen.helpers import zen_internals
from aikido_zen.helpers.ip_matcher import IPMatcher
from aikido_zen.helpers.logging import logger
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

    def update(
        self,
        blocked_ip_entries,
        allowed_ip_entries,
        blocked_user_agents,
        monitored_ip_entries,
        monitored_user_agents,
        user_agent_details,
    ):
        """Replaces all lists together, so lists from different updates never mix."""
        # Data that is not a list of IPs is broken, so the current lists stay in place.
        for entry in blocked_ip_entries + allowed_ip_entries:
            if entry.get("ips") is not None and not isinstance(entry.get("ips"), list):
                logger.error(
                    "Zen failed to update the firewall lists: "
                    "IP list %s has no list of IPs.",
                    entry.get("source"),
                )
                return
        blocked_ips = list(map(parse_ip_entry, blocked_ip_entries))
        monitored_ips = list(map(parse_ip_entry, monitored_ip_entries))
        # An allowlist without IPs would block every visitor, so it is skipped.
        allowed_ips = [
            entry
            for entry in map(parse_ip_entry, allowed_ip_entries)
            if not entry["iplist"].is_empty()
        ]
        ip_lists = blocked_ips + monitored_ips + allowed_ips
        # Aikido only sends valid networks, so an invalid one means the data is broken.
        for entry in ip_lists:
            rejected_count = entry["iplist"].rejected_count()
            if rejected_count:
                logger.error(
                    "IP list %s has %s invalid network(s), which Zen skipped.",
                    entry["source"],
                    rejected_count,
                )
        # A list that failed to build matches no IP, so the current lists stay in place.
        failed = [e for e in blocked_ips + allowed_ips if not e["iplist"].is_built()]
        if failed:
            if zen_internals.has_ip_matcher():
                logger.error(
                    "Zen failed to update the firewall lists: "
                    "IP list %s could not be built.",
                    failed[0]["source"],
                )
                return
            # Without the library no list builds, and an allowlist would block everyone.
            allowed_ips = []
        # Monitored lists only count hits, so one that failed to build is just dropped.
        monitored_ips = [e for e in monitored_ips if e["iplist"].is_built()]
        self.blocked_ips = blocked_ips
        self.allowed_ips = allowed_ips
        self.monitored_ips = monitored_ips
        self.set_blocked_user_agents(blocked_user_agents)
        self.set_monitored_user_agents(monitored_user_agents)
        self.set_user_agent_details(user_agent_details)

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
    ips = entry.get("ips")
    return {
        "key": entry.get("key"),
        "source": entry.get("source"),
        "description": entry.get("description") or "a firewall list",
        # A string or object would be read as single characters or keys, not networks.
        "iplist": IPMatcher(ips if isinstance(ips, list) else []),
    }
