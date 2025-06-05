import aikido_zen.helpers.get_current_unixtime_ms as t
from aikido_zen.storage.statistics.operations import Operations


class Statistics:
    """
    Keeps track of total and aborted requests
    and total and blocked attacks
    """

    def __init__(self):
        self.total_hits = 0
        self.attacks_detected = 0
        self.attacks_blocked = 0
        self.started_at = t.get_unixtime_ms()
        self.operations = Operations()

    def clear(self):
        self.total_hits = 0
        self.attacks_detected = 0
        self.attacks_blocked = 0
        self.started_at = t.get_unixtime_ms()
        self.operations.clear()

    def increment_total_hits(self):
        self.total_hits += 1

    def on_detected_attack(self, blocked, operation):
        self.attacks_detected += 1
        if blocked:
            self.attacks_blocked += 1
        self.operations.on_detected_attack(blocked, operation)

    def get_record(self):
        current_time = t.get_unixtime_ms()
        return {
            "startedAt": self.started_at,
            "endedAt": current_time,
            "requests": {
                "total": self.total_hits,
                "aborted": 0,  # statistic currently not in use
                "attacksDetected": {
                    "total": self.attacks_detected,
                    "blocked": self.attacks_blocked,
                },
            },
            "operations": dict(self.operations),
        }

    def import_from_record(self, record):
        attacks_detected = record.get("requests", {}).get("attacksDetected", {})
        self.total_hits += record.get("requests", {}).get("total", 0)
        self.attacks_detected += attacks_detected.get("total", 0)
        self.attacks_blocked += attacks_detected.get("blocked", 0)
        self.operations.update(record.get("operations", {}))

    def empty(self):
        if self.total_hits > 0:
            return False
        if self.attacks_detected > 0:
            return False
        if len(self.operations) > 0:
            return False
        return True
