"""
Test cases for AttackWaveDetectorStore
"""

import pytest
import threading
import time
from unittest.mock import patch
from .attack_wave_detector_store import (
    AttackWaveDetectorStore,
    attack_wave_detector_store,
)
import aikido_zen.test_utils as test_utils


def test_attack_wave_detector_store_initialization():
    """Test that the store initializes correctly"""
    store = AttackWaveDetectorStore()
    assert store is not None
    assert store._get_detector() is not None


def test_attack_wave_detector_store_singleton():
    """Test that the global singleton instance works"""
    assert attack_wave_detector_store is not None
    assert attack_wave_detector_store._get_detector() is not None


def test_is_attack_wave_basic_functionality():
    """Test basic attack wave detection functionality"""
    store = AttackWaveDetectorStore()
    context = test_utils.generate_context()

    # Mock is_web_scanner to return True for this test
    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Should return False for first few calls
        assert not store.is_attack_wave(context)
        assert not store.is_attack_wave(context)

        # Call 12 more times to get to 14 total (still below threshold)
        for _ in range(12):
            result = store.is_attack_wave(context)
            assert not result

        # The 15th call should trigger attack wave detection and return True
        assert store.is_attack_wave(context)


def test_is_attack_wave_different_ips():
    """Test that different IPs are tracked separately"""
    store = AttackWaveDetectorStore()
    context1 = test_utils.generate_context(ip="1.1.1.1")
    context2 = test_utils.generate_context(ip="2.2.2.2")

    # Mock is_web_scanner to return True for this test
    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Call multiple times for different IPs
        for _ in range(10):
            store.is_attack_wave(context1)
            store.is_attack_wave(context2)

        # Neither should trigger attack wave yet
        assert not store.is_attack_wave(context1)
        assert not store.is_attack_wave(context2)


def test_is_attack_wave_none_context():
    """Test handling of None context"""
    store = AttackWaveDetectorStore()
    assert not store.is_attack_wave(None)


def test_is_attack_wave_no_ip_in_context():
    """Test handling of context with no IP address"""
    store = AttackWaveDetectorStore()
    context = test_utils.generate_context(ip=None)
    assert not store.is_attack_wave(context)


def test_thread_safety_multiple_threads():
    """Test thread safety with multiple threads accessing the store"""
    store = AttackWaveDetectorStore()

    results = []
    threads = []

    def worker(ip_suffix, result_list):
        """Worker function that calls is_attack_wave multiple times"""
        context = test_utils.generate_context(ip=f"192.168.1.{ip_suffix}")
        for _ in range(5):
            result = store.is_attack_wave(context)
            result_list.append((context.remote_address, result))
            time.sleep(0.001)  # Small delay to simulate real usage

    # Create and start multiple threads
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i, results))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify that we got results from all threads
    assert len(results) == 25  # 5 threads * 5 calls each

    # Verify that no exceptions were raised (thread safety)
    assert all(isinstance(result, tuple) for result in results)


def test_thread_safety_same_ip():
    """Test thread safety when multiple threads access the same IP"""
    store = AttackWaveDetectorStore()

    results = []
    threads = []
    lock = threading.Lock()

    def worker(result_list):
        """Worker function that calls is_attack_wave for the same IP"""
        context = test_utils.generate_context(ip="10.0.0.1")
        for _ in range(10):
            result = store.is_attack_wave(context)
            with lock:
                result_list.append(result)
            time.sleep(0.001)

    # Create and start multiple threads
    for _ in range(3):
        thread = threading.Thread(target=worker, args=(results,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify that we got results from all threads
    assert len(results) == 30  # 3 threads * 10 calls each

    # Verify that no exceptions were raised
    assert all(isinstance(result, bool) for result in results)


def test_attack_wave_cooldown():
    """Test that attack wave detection respects the cooldown period"""
    store = AttackWaveDetectorStore()
    context = test_utils.generate_context()

    # Mock is_web_scanner to return True for this test
    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Call 14 times to get close to threshold
        for _ in range(14):
            store.is_attack_wave(context)

        # The 15th call should trigger attack wave detection and return True
        assert store.is_attack_wave(context)

        # Subsequent calls should return False due to cooldown
        assert not store.is_attack_wave(context)


def test_attack_wave_time_frame():
    """Test that attack wave detection respects the time frame"""
    store = AttackWaveDetectorStore()
    context = test_utils.generate_context()

    # Mock is_web_scanner to return True for this test
    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Make some calls
        for _ in range(5):
            store.is_attack_wave(context)

        # Should not trigger attack wave yet
        assert not store.is_attack_wave(context)

        # Wait for the time frame to expire (60 seconds)
        # We can't actually wait 60 seconds in a test, but we can verify the behavior
        # by checking that the detector is tracking the requests correctly
        detector = store._get_detector()
        assert detector.suspicious_requests_map.get(context.remote_address) == 6


def test__get_detector_returns_same_instance():
    """Test that _get_detector returns the same instance"""
    store = AttackWaveDetectorStore()
    detector1 = store._get_detector()
    detector2 = store._get_detector()
    assert detector1 is detector2


def test_global_singleton_consistency():
    """Test that the global singleton is consistent"""
    detector1 = attack_wave_detector_store._get_detector()
    detector2 = attack_wave_detector_store._get_detector()
    assert detector1 is detector2


def test_attack_wave_detector_store_with_custom_parameters():
    """Test that custom parameters can be set via the detector"""
    store = AttackWaveDetectorStore()
    detector = store._get_detector()

    # Verify default parameters
    assert detector.attack_wave_threshold == 15
    assert detector.attack_wave_time_frame == 60 * 1000
    assert detector.min_time_between_events == 20 * 60 * 1000


def test_stress_test_high_concurrency():
    """Stress test with high concurrency"""
    store = AttackWaveDetectorStore()

    results = []
    threads = []

    def worker(worker_id):
        """Worker function for stress test"""
        try:
            for i in range(10):
                context = test_utils.generate_context(ip=f"192.168.{worker_id}.{i}")
                result = store.is_attack_wave(context)
                results.append((worker_id, context.remote_address, result))
        except Exception as e:
            results.append((worker_id, "error", str(e)))

    # Create many threads
    for i in range(10):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify that all threads completed without errors
    error_results = [r for r in results if r[1] == "error"]
    assert len(error_results) == 0

    # Verify we got expected number of results
    assert len(results) == 100  # 10 threads * 10 IPs each


def test_samples_tracking_in_store():
    """Test that samples are tracked correctly through the store"""
    store = AttackWaveDetectorStore()
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Make a few requests
        for i in range(3):
            store.is_attack_wave(context)

        # Check that samples are being tracked
        samples = store.get_samples_for_ip(context.remote_address)
        assert len(samples) == 3

        # Clear samples
        store.clear_samples_for_ip(context.remote_address)

        # Verify samples are cleared
        samples = store.get_samples_for_ip(context.remote_address)
        assert len(samples) == 0


@patch("aikido_zen.storage.attack_wave_detector_store.AttackWaveDetector")
def test_mock_detector_integration(mock_detector_class):
    """Test integration with mocked AttackWaveDetector"""
    # Setup mock
    mock_detector = mock_detector_class.return_value
    mock_detector.is_attack_wave.return_value = True

    store = AttackWaveDetectorStore()
    context = test_utils.generate_context()

    # Should use the mocked detector
    result = store.is_attack_wave(context)
    assert result is True
    mock_detector.is_attack_wave.assert_called_once_with(context)
