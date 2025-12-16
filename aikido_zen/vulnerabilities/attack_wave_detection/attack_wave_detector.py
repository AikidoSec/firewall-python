import aikido_zen.helpers.get_current_unixtime_ms as internal_time
from aikido_zen.ratelimiting.lru_cache import LRUCache
from aikido_zen.context import Context
from aikido_zen.vulnerabilities.attack_wave_detection.is_web_scanner import (
    is_web_scanner,
)


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
        # Track samples for metadata reporting
        self.samples_map = LRUCache(
            max_items=self.max_lru_entries,
            time_to_live_in_ms=self.attack_wave_time_frame,
        )

    def is_attack_wave(self, context: Context) -> bool:
        """
        Function gets called with context to check if there is an attack wave request.
        """
        if not context or not context.remote_address:
            return False
        ip = context.remote_address

        if self.sent_events_map.get(ip) is not None:
            return False

        if not is_web_scanner(context):
            return False

        # Increment suspicious requests count -> there is a new or first suspicious request
        suspicious_requests = (self.suspicious_requests_map.get(ip) or 0) + 1
        self.suspicious_requests_map.set(ip, suspicious_requests)

        samples = self.samples_map.get(ip) or []

        # There's no use in reporting a sample twice.
        sample_exists = False
        for existing_sample in samples:
            if (
                existing_sample["method"] == context.method
                and existing_sample["url"] == context.url
            ):
                sample_exists = True
                break
        if not sample_exists:
            samples.append(
                {
                    "method": context.method,
                    "url": context.url,
                }
            )

        # Keep only the most recent samples (limit to avoid memory issues)
        if len(samples) > 10:
            samples = samples[-10:]
        self.samples_map.set(ip, samples)

        if suspicious_requests < self.attack_wave_threshold:
            return False

        # Mark event as sent
        self.sent_events_map.set(ip, internal_time.get_unixtime_ms(monotonic=True))
        return True

    def get_samples_for_ip(self, ip: str):
        return self.samples_map.get(ip) or []

    def clear_samples_for_ip(self, ip: str):
        self.samples_map.delete(ip)
