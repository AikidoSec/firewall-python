from aikido_zen.helpers import zen_internals
from aikido_zen.helpers.ip_matcher import IPMatcher
from aikido_zen.helpers.logging import logger
import regex as re

from aikido_zen.helpers.net.is_private_ip import is_private_ip


class FirewallLists:
    def __init__(self):
        self.blocked_ips = []
        self.allowed_ips = []
        self.blocked_user_agent_regex = None

    def update(self, blocked_ip_entries, allowed_ip_entries, blocked_user_agents):
        """Replaces all lists together, so lists from different updates never mix."""
        blocked_ips = list(map(parse_ip_entry, blocked_ip_entries))
        # An allowlist without IPs would block every visitor, so it is skipped.
        allowed_ips = [
            entry
            for entry in map(parse_ip_entry, allowed_ip_entries)
            if not entry["iplist"].is_empty()
        ]
        # Aikido only sends valid networks, so an invalid one means the data is broken.
        for entry in blocked_ips + allowed_ips:
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
        self.blocked_ips = blocked_ips
        self.allowed_ips = allowed_ips
        self.set_blocked_user_agents(blocked_user_agents)

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
        "source": entry.get("source"),
        "description": entry.get("description") or "a firewall list",
        "iplist": IPMatcher(entry.get("ips")),
    }
