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
        try:
            res = requests.post(
                self.reporting_url + "api/runtime/events",
                data=event,
                timeout=timeout_in_sec,
                headers=get_headers(token),
            )
        except requests.exceptions.Timeout:
            return {"success": False, "error": "timeout"}
        except Exception as e:
            raise e
        return self.to_api_response(res)


def get_headers(token):
    """Returns headers"""
    return {"Content-Type": "application/json", "Authorization": str(token)}