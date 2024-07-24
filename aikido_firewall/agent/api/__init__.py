""" 
init.py file for api/ folder. Includes abstract class ReportingApi
"""

import json


class ReportingApi:
    """This is the super class for the reporting API's"""

    def to_api_response(self, status, data):
        """Converts results into an Api response obj"""
        if status == 429:
            return {"success": False, "error": "rate_limited"}
        elif status == 401:
            return {"success": False, "error": "invalid_token"}
        try:
            return json.loads(data)
        except Exception:
            return {"success": False, "error": "unknown_error"}

    def report(self, token, event, timeout_in_sec):
        """Report event to aikido server"""
