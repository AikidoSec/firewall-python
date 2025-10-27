"""
Exports ServiceConfig class
"""

from typing import Pattern

from aikido_zen.helpers.ip_matcher import IPMatcher
from aikido_zen.helpers.match_endpoints import match_endpoints


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

        # Create an IPMatcher instance for each endpoint
        for endpoint in self.endpoints:
            if not "allowedIPAddresses" in endpoint:
                #  This feature is not supported by the current aikido server version
                continue
            if (
                not isinstance(endpoint["allowedIPAddresses"], list)
                or len(endpoint["allowedIPAddresses"]) == 0
            ):
                #  Skip empty allowlist
                continue

            endpoint["allowedIPAddresses"] = IPMatcher(endpoint["allowedIPAddresses"])

    def get_endpoints(self, route_metadata):
        """
        Gets the endpoint that matches the current context
        route_metadata object includes route, url and method
        """
        return match_endpoints(route_metadata, self.endpoints)

    def set_bypassed_ips(self, bypassed_ips):
        """Creates an IPMatcher from the given bypassed ip set"""
        self.bypassed_ips = IPMatcher()
        for ip in bypassed_ips:
            self.bypassed_ips.add(ip)

    def is_bypassed_ip(self, ip):
        """Checks if the IP is on the bypass list"""
        return self.bypassed_ips.has(ip)
