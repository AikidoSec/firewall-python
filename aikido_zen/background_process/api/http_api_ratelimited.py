"""
Exports ReportingApiHTTPRatelimited
"""

import aikido_zen.background_process.api.http_api as http_api
import aikido_zen.helpers.get_current_unixtime_ms as t


class ReportingApiHTTPRatelimited(http_api.ReportingApiHTTP):
    """HTTP Reporting API that has ratelimiting support"""

    def __init__(self, reporting_url, max_events_per_interval, interval_in_ms):
        super().__init__(reporting_url)
        self.interval_in_ms = interval_in_ms
        self.max_events_per_interval = max_events_per_interval
        self.events = []

    def report(self, token, event, timeout_in_sec):
        if event["type"] == "detected_attack":
            # Remove all outdated events :
            current_time = t.get_unixtime_ms()

            def event_in_interval_filter(e):
                return e["time"] > current_time - self.interval_in_ms

            self.events = list(filter(event_in_interval_filter, self.events))

            # Check if interval is exceeded :
            if len(self.events) >= self.max_events_per_interval:
                return {"success": False, "error": "max_attacks_reached"}

            self.events.append(event)
        return super().report(token, event, timeout_in_sec)
