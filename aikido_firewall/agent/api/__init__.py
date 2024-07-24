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


class Token:
    """Class that encapsulates the token"""

    def __init__(self, token):
        if not isinstance(token, str):
            raise ValueError("Token should be an instance of string")
        if len(token) == 0:
            raise ValueError("Token cannot be an empty string")
        self.token = token

    def __str__(self):
        return self.token
