"""
?
"""

from aikido_firewall.helpers.match_endpoint import match_endpoint


class ReporterConfig:
    """Class holding the config of the reporter"""

    def __init__(self, endpoints, last_updated_at):
        self.endpoints = [endpoint for endpoint in endpoints if not endpoint["graphql"]]
        self.last_updated_at = last_updated_at

    def get_endpoint(self, context):
        """
        Gets the endpoint that matches the current context
        """
        return match_endpoint(context, self.endpoints)
