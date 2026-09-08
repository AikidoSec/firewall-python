""" 
init.py file for api/ folder. Includes abstract class ReportingApi
"""

from aikido_zen.background_process.requests.make_request import Response
from aikido_zen.helpers.logging import logger


class ReportingApi:
    """This is the super class for the reporting API's"""

    @staticmethod
    def to_api_response(res: Response):
        """Converts results into an Api response obj"""
        status = res.status_code
        if status == 429:
            return {"success": False, "error": "rate_limited"}
        if status == 401:
            return {"success": False, "error": "invalid_token"}
        if status == 200:
            try:
                return res.json()
            except Exception as e:
                logger.debug(
                    "Parsing JSON response from core failed: %s (body=%s)",
                    str(e),
                    res.text,
                )
                return {"success": False, "error": "json_parsing_failed"}
        logger.debug("Parsing response from core failed: [%s] %s", status, res.text)
        return {"success": False, "error": "status_code_not_200"}

    def report(self, token, event, timeout_in_sec):
        """Report event to aikido server"""

    def fetch_firewall_lists(self, token):
        """Fetches the different lists from aikido's servers"""
