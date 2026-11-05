"""
Exports the HTTP API class
"""

import aikido_zen.background_process.requests as requests
from aikido_zen.background_process.api import ReportingApi
from aikido_zen.background_process.requests.errors import TimeoutExceeded
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_zen.helpers.logging import logger


class ReportingApiHTTP(ReportingApi):
    """HTTP Reporting API"""

    def __init__(
        self, reporting_url, max_events_per_interval=100, interval_in_ms=60 * 60 * 1000
    ):
        self.reporting_url = reporting_url
        self.max_events_per_interval = max_events_per_interval
        self.interval_in_ms = interval_in_ms
        self.attack_times = []

    def report(self, token, event, timeout_in_sec):
        if event.get("type") == "detected_attack":
            window_start = get_unixtime_ms() - self.interval_in_ms
            self.attack_times = [
                attack_time
                for attack_time in self.attack_times
                if attack_time > window_start
            ]

            if len(self.attack_times) >= self.max_events_per_interval:
                return {"success": False, "error": "max_attacks_reached"}

            self.attack_times.append(event["time"])

        try:
            res = requests.post(
                self.reporting_url + "api/runtime/events",
                json=event,
                timeout=timeout_in_sec,
                headers=get_headers(token),
            )
        except TimeoutExceeded:
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error("Failed to report event : %s(%s)", str(e.__class__), str(e))
            return {"success": False, "error": "unknown"}
        return self.to_api_response(res)

    def fetch_firewall_lists(self, token):
        """
        Fetches firewall lists from aikido's servers
        If successful the current API returns :
        - `allowedIPAddresses` : An array with iplist entries which are the only ones allowed
        - `blockedIPAddresses` : An array with iplist entries that are blocked
        - `monitoredIPAddresses` : An array with iplist entries that are counted but not blocked
        - `blockedUserAgents` : A string with a simple regex to match user agents with
        - `monitoredUserAgents` : A string with a simple regex to match monitored user agents with
        - `userAgentDetails` : An array of {key, pattern}, to report which user agent matched
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
        except TimeoutExceeded:
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error("Failed to fetch firewall lists: %s", str(e))
            return {"success": False, "error": "unknown"}
        return self.to_api_response(res)


def get_headers(token):
    """Returns headers"""
    return {"Content-Type": "application/json", "Authorization": str(token)}
