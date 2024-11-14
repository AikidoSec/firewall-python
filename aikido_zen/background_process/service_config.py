"""
Exports ServiceConfig class
"""

from aikido_zen.helpers.add_ip_address_to_blocklist import add_ip_address_to_blocklist
from aikido_zen.helpers.match_endpoints import match_endpoints
from aikido_zen.helpers.blocklist import BlockList


class ServiceConfig:
    """Class holding the config of the connection_manager"""

    def __init__(
        self,
        endpoints,
        last_updated_at,
        blocked_uids,
        bypassed_ips,
        received_any_stats,
        blocked_ips,
    ):
        self.endpoints = [
            endpoint for endpoint in endpoints if not endpoint.get("graphql")
        ]
        self.last_updated_at = last_updated_at
        self.bypassed_ips = set(bypassed_ips)
        self.blocked_uids = set(blocked_uids)
        self.received_any_stats = bool(received_any_stats)
        self.blocked_ips = BlockList()
        for blocked_ip in blocked_ips:
            add_ip_address_to_blocklist(blocked_ip, self.blocked_ips)

    def get_endpoints(self, route_metadata):
        """
        Gets the endpoint that matches the current context
        route_metadata object includes route, url and method
        """
        return match_endpoints(route_metadata, self.endpoints)

    def is_bypassed_ip(self, ip):
        """Checks if the IP is on the bypass list"""
        return ip in self.bypassed_ips

    def is_blocked_ip(self, ip):
        return self.blocked_ips.is_blocked(ip)
