"""
?
"""

from aikido_firewall.helpers.match_endpoint import match_endpoint


class ServiceConfig:
    """Class holding the config of the reporter"""

    def __init__(self, endpoints, last_updated_at, blocked_uids, bypassed_ips):
        self.endpoints = [endpoint for endpoint in endpoints if not endpoint["graphql"]]
        self.last_updated_at = last_updated_at
        self.bypassed_ips = set(bypassed_ips)
        self.blocked_uids = set(blocked_uids)

    def get_endpoint(self, route_metadata):
        """
        Gets the endpoint that matches the current context
        route_metadata object includes route, url and method
        """
        return match_endpoint(route_metadata, self.endpoints)

    def get_endpoints(self, route_metadata):
        """
        Gets the endpoint that matches the current context
        route_metadata object includes route, url and method
        """
        return match_endpoint(route_metadata, self.endpoints, multi=True)

    def is_bypassed_ip(self, ip):
        """Checks if the IP is on the bypass list"""
        return ip in self.bypassed_ips

    def is_user_blocked(self, user_id):
        """Checks if the user id is blocked"""
        return user_id in self.blocked_uids
