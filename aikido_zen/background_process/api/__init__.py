""" 
init.py file for api/ folder. Includes abstract class ReportingApi
"""

import json
from aikido_zen.helpers.logging import logger


class ReportingApi:
    """This is the super class for the reporting API's"""

    def to_api_response(self, res):
        """Converts results into an Api response obj"""
        status = res.status_code
        if status == 429:
            return {"success": False, "error": "rate_limited"}
        elif status == 401:
            return {"success": False, "error": "invalid_token"}
        elif status == 200:
            try:
                return json.loads(res.text)
            except Exception as e:
                logger.debug(e)
                logger.debug(res.text)
        return {"success": False, "error": "unknown_error"}

    def report(self, token, event, timeout_in_sec):
        """Report event to aikido server"""

    def fetch_blocked_ips(self, token):
        """Fetches blocked IPs from aikido server"""
