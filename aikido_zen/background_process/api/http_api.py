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


def get_headers(token):
    """Returns headers"""
    return {"Content-Type": "application/json", "Authorization": str(token)}
