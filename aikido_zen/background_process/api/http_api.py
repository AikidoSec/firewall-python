"""
Exports the HTTP API class
"""

from aikido_zen.background_process.api import ReportingApi
from aikido_zen.background_process.api.helpers import InternalRequest, Response


class ReportingApiHTTP(ReportingApi):
    """HTTP Reporting API"""

    def __init__(self, reporting_url):
        self.reporting_url = reporting_url

    def report(self, token, event, timeout_in_sec) -> Response:
        REPORT_EVENTS_URL = self.reporting_url + "api/runtime/events"
        return InternalRequest.post(
            REPORT_EVENTS_URL,
            json=event,
            timeout=timeout_in_sec,
            headers=get_headers(token),
        )

    def fetch_firewall_lists(self, token) -> Response:
        """
        Fetches firewall lists from Aikido's servers
        If successful the current API returns :
        - `allowedIPAddresses` : An array with iplist entries which are the only ones allowed
        - `blockedIPAddresses` : An array with iplist entries that are blocked
        - `blockedUserAgents` : A string with a simple regex to match user agents with
        """
        FIREWALL_LISTS_URL = self.reporting_url + "api/runtime/firewall/lists"
        headers = {
            # We need to set the Accept-Encoding header to "gzip" to receive the response in gzip format
            "Accept-Encoding": "gzip",
            "Authorization": str(token),
        }
        return InternalRequest.get(FIREWALL_LISTS_URL, headers=headers, timeout=20)


def get_headers(token):
    """Returns headers"""
    return {"Authorization": str(token)}
