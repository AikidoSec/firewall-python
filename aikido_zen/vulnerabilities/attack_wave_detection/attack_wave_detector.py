import aikido_zen.helpers.get_current_unixtime_ms as internal_time
from aikido_zen.ratelimiting.lru_cache import LRUCache


class AttackWaveDetector:
    def __init__(
        self,
        attack_wave_threshold: int = 15,
        attack_wave_time_frame: int = 60 * 1000,  # 1 minute in ms
        min_time_between_events: int = 20 * 60 * 1000,  # 20 minutes in ms
        max_lru_entries: int = 10_000,
    ):
        self.attack_wave_threshold = attack_wave_threshold
        self.attack_wave_time_frame = attack_wave_time_frame
        self.min_time_between_events = min_time_between_events
        self.max_lru_entries = max_lru_entries

        self.suspicious_requests_map = LRUCache(
            max_items=self.max_lru_entries,
            time_to_live_in_ms=self.attack_wave_time_frame,
        )
        self.sent_events_map = LRUCache(
            max_items=self.max_lru_entries,
            time_to_live_in_ms=self.min_time_between_events,
        )

    def check(self, ip: str) -> bool:
        """
        Function gets called with IP if there is an attack wave request.
        """
        if not ip:
            return False

        # Check if an event was sent recently
        if self.sent_events_map.get(ip) is not None:
            return False

        # Increment suspicious requests count -> there is a new or first suspicious request
        suspicious_requests = (self.suspicious_requests_map.get(ip) or 0) + 1
        self.suspicious_requests_map.set(ip, suspicious_requests)

        if suspicious_requests < self.attack_wave_threshold:
            return False

        # Mark event as sent
        self.sent_events_map.set(ip, internal_time.get_unixtime_ms(monotonic=True))
        return True
