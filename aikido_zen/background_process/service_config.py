"""
Exports ServiceConfig class
"""

from aikido_zen.helpers.ip_matcher import IPMatcher
from aikido_zen.helpers.match_endpoints import match_endpoints


class ServiceConfig:

    def __init__(self):
        self.endpoints = []
        self.bypassed_ips = IPMatcher()
        self.blocked_uids = set()
        self.last_updated_at = -1
        self.received_any_stats = False

    def set_endpoints(self, endpoints):
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
        """Creates a new IPMatcher from the given bypassed ip set"""
        self.bypassed_ips = IPMatcher()
        for ip in bypassed_ips:
            self.bypassed_ips.add(ip)

    def is_bypassed_ip(self, ip):
        """Checks if the IP is on the bypass list"""
        return self.bypassed_ips.has(ip)

    def set_blocked_user_ids(self, blocked_user_ids):
        self.blocked_uids = set(blocked_user_ids)

    def enable_received_any_stats(self):
        self.received_any_stats = True

    def set_last_updated_at(self, last_updated_at: int):
        self.last_updated_at = last_updated_at
