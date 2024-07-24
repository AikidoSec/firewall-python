"""
Exports the HTTP API class
"""

import requests
from aikido_firewall.agent.api import ReportingApi


class ReportingApiHTTP(ReportingApi):
    """HTTP Reporting API"""

    def __init__(self, reporting_url):
        self.reporting_url = reporting_url

    def report(self, token, event, timeout_in_sec):
        res = requests.post(
            self.reporting_url + "api/runtime/events",
            data=event,
            timeout=timeout_in_sec,
            headers=get_headers(token),
        )


def get_headers(token):
    """Returns headers"""
    return {"Content-Type": "application/json", "Authorization": str(token)}
