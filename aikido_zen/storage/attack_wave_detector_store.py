import threading
from aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector import (
    AttackWaveDetector,
)


class AttackWaveDetectorStore:
    def __init__(self):
        self._detector = AttackWaveDetector()
        self._lock = threading.RLock()  # Reentrant lock for thread safety

    def is_attack_wave(self, ip: str) -> bool:
        with self._lock:
            return self._detector.is_attack_wave(ip)

    def _get_detector(self):
        """Used in testing (internal)"""
        return self._detector


attack_wave_detector_store = AttackWaveDetectorStore()
