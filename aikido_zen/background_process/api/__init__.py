""" 
init.py file for api/ folder. Includes abstract class ReportingApi
"""

from aikido_zen.background_process.api.helpers import Response


class ReportingApi:
    """This is the super class for the reporting API's"""

    def report(self, token, event, timeout_in_sec) -> Response:
        """Report event to aikido server"""

    def fetch_firewall_lists(self, token) -> Response:
        """Fetches the different lists from aikido's servers"""
