"""
Exports ServiceConfig class
"""

from aikido_zen.helpers.add_ip_address_to_blocklist import add_ip_address_to_blocklist
from aikido_zen.helpers.match_endpoints import match_endpoints
from aikido_zen.helpers.blocklist import BlockList
from aikido_zen.helpers.logging import logger


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
        self.bypassed_ips = BlockList()
        for ip in bypassed_ips:
            add_ip_address_to_blocklist(ip, self.bypassed_ips)

        self.blocked_uids = set(blocked_uids)
        self.received_any_stats = bool(received_any_stats)
        self.set_blocked_ips(blocked_ips)

    def get_endpoints(self, route_metadata):
        """
        Gets the endpoint that matches the current context
        route_metadata object includes route, url and method
        """
        return match_endpoints(route_metadata, self.endpoints)

    def is_bypassed_ip(self, ip):
        """Checks if the IP is on the bypass list"""
        return self.bypassed_ips.is_blocked(ip)

    def is_blocked_ip(self, ip):
        for entry in self.blocked_ips:
            if entry["blocklist"].is_blocked(ip):
                return entry["description"]
        return False

    def set_blocked_ips(self, blocked_ip_entries):
        self.blocked_ips = list()
        # Go over entries : {"source": "example", "description": "Example description", "ips": []}
        for entry in blocked_ip_entries:
            # Create a blocklist of the ip addresses and ip ranges :
            blocklist = BlockList()
            for ip in entry["ips"]:
                add_ip_address_to_blocklist(ip, blocklist)

            self.blocked_ips.append(
                {
                    "source": entry.get("source"),
                    "description": entry.get("description"),
                    "blocklist": blocklist,
                }
            )
