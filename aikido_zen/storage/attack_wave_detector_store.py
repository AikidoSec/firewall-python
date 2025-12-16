import threading
from aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector import (
    AttackWaveDetector,
)
from aikido_zen.context import Context


class AttackWaveDetectorStore:
    def __init__(self):
        self._detector = AttackWaveDetector()
        self._lock = threading.RLock()  # Reentrant lock for thread safety

    def is_attack_wave(self, context: Context) -> bool:
        with self._lock:
            return self._detector.is_attack_wave(context)

    def get_samples_for_ip(self, ip: str):
        """Get samples for a specific IP address"""
        with self._lock:
            return self._detector.get_samples_for_ip(ip)

    def clear_samples_for_ip(self, ip: str):
        """Clear samples for a specific IP address"""
        with self._lock:
            return self._detector.clear_samples_for_ip(ip)

    def _get_detector(self):
        """Used in testing (internal)"""
        return self._detector


attack_wave_detector_store = AttackWaveDetectorStore()
