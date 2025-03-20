"""
Exports ServiceConfig class
"""

from typing import Pattern

import regex as re
from aikido_zen.helpers.add_ip_address_to_blocklist import add_ip_address_to_blocklist
from aikido_zen.helpers.match_endpoints import match_endpoints
from aikido_zen.helpers.iplist import IPList


# noinspection PyAttributeOutsideInit
class ServiceConfig:
    """Class holding the config of the connection_manager"""

    def __init__(
        self,
        endpoints,
        last_updated_at: int,
        blocked_uids,
        bypassed_ips,
        received_any_stats: bool,
    ):
        # Init the class using update function :
        self.update(
            endpoints, last_updated_at, blocked_uids, bypassed_ips, received_any_stats
        )
        self.blocked_ips = []
        self.allowed_ips = []
        self.blocked_user_agent_regex: Pattern = None

    def update(
        self,
        endpoints,
        last_updated_at: int,
        blocked_uids,
        bypassed_ips,
        received_any_stats: bool,
    ):
        self.last_updated_at = last_updated_at
        self.received_any_stats = bool(received_any_stats)
        self.blocked_uids = set(blocked_uids)
        self.set_endpoints(endpoints)
        self.set_bypassed_ips(bypassed_ips)

    def set_endpoints(self, endpoints):
        """Sets non-graphql endpoints"""
        self.endpoints = [
            endpoint for endpoint in endpoints if not endpoint.get("graphql")
        ]

    def get_endpoints(self, route_metadata):
        """
        Gets the endpoint that matches the current context
        route_metadata object includes route, url and method
        """
        return match_endpoints(route_metadata, self.endpoints)

    def set_bypassed_ips(self, bypassed_ips):
        """Creates an IPList from the given bypassed ip set"""
        self.bypassed_ips = IPList()
        for ip in bypassed_ips:
            add_ip_address_to_blocklist(ip, self.bypassed_ips)

    def is_bypassed_ip(self, ip):
        """Checks if the IP is on the bypass list"""
        return self.bypassed_ips.matches(ip)

    def set_blocked_ips(self, blocked_ip_entries):
        self.blocked_ips = parse_ip_entries(blocked_ip_entries)

    def set_allowed_ips(self, allowed_ip_entries):
        self.allowed_ips = parse_ip_entries(allowed_ip_entries)

    def is_blocked_ip(self, ip):
        for entry in self.blocked_ips:
            if entry["iplist"].matches(ip):
                return entry["description"]
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
        return self.blocked_user_agent_regex.match(ua)


def parse_ip_entries(ip_entries):
    """
    Converts ip entries: {"source": "example", "description": "Example description", "ips": []}
    """
    for entry in ip_entries:
        # Create an IPList for the addresses and ranges provided in `ips` :
        entry["iplist"] = IPList()
        for ip in entry["ips"]:
            add_ip_address_to_blocklist(ip, entry["iplist"])
        del entry["ips"]  # Delete the now converted `ips` list.
    return ip_entries
