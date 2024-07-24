"""
Exports the HTTP API class
"""

from aikido_firewall.agent.api import ReportingApi


class ReportingApiHTTP(ReportingApi):
    """HTTP Reporting API"""

    def __init__(self, reporting_url):
        self.reporting_url = reporting_url

    def report(self, token, event, timeout_in_ms):
        print("Do something here")
