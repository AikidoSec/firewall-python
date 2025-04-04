"""
Exports the HTTP API class
"""

import requests
from aikido_zen.background_process.api import ReportingApi
from aikido_zen.helpers.logging import logger


class ReportingApiHTTP(ReportingApi):
    """HTTP Reporting API"""

    def __init__(self, reporting_url):
        self.reporting_url = reporting_url

    def report(self, token, event, timeout_in_sec):
        try:
            res = requests.post(
                self.reporting_url + "api/runtime/events",
                json=event,
                timeout=timeout_in_sec,
                headers=get_headers(token),
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(e)
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(e)
            return {"success": False, "error": "unknown"}
        return self.to_api_response(res)

    def fetch_firewall_lists(self, token):
        """
        Fetches firewall lists from aikido's servers
        If successful the current API returns :
        - `allowedIPAddresses` : An array with iplist entries which are the only ones allowed
        - `blockedIPAddresses` : An array with iplist entries that are blocked
        - `blockedUserAgents` : A string with a simple regex to match user agents with
        """
        try:
            res = requests.get(
                self.reporting_url + "api/runtime/firewall/lists",
                timeout=20,
                headers={
                    # We need to set the Accept-Encoding header to "gzip" to receive the response in gzip format
                    "Accept-Encoding": "gzip",
                    "Authorization": str(token),
                },
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(e)
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(e)
            return {"success": False, "error": "unknown"}
        return self.to_api_response(res)


def get_headers(token):
    """Returns headers"""
    return {"Content-Type": "application/json", "Authorization": str(token)}
