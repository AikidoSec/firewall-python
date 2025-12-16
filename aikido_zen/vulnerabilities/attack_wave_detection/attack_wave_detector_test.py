import pytest
from unittest.mock import patch
from .attack_wave_detector import AttackWaveDetector
import aikido_zen.test_utils as test_utils


def new_attack_wave_detector():
    return AttackWaveDetector(
        attack_wave_threshold=6,
        attack_wave_time_frame=60 * 1000,
        min_time_between_events=60 * 60 * 1000,
        max_lru_entries=10_000,
    )


# Mock for get_unixtime_ms
def mock_get_unixtime_ms(monotonic=True, mock_time=0):
    return mock_time


def test_no_context():
    detector = new_attack_wave_detector()
    assert not detector.is_attack_wave(None)


def test_no_ip_address_in_context():
    detector = new_attack_wave_detector()
    context = test_utils.generate_context(ip=None)
    assert not detector.is_attack_wave(context)


def test_a_web_scanner():
    detector = new_attack_wave_detector()
    context = test_utils.generate_context()

    # Mock is_web_scanner to return True for this test
    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        # Is true because the threshold is 6
        assert detector.is_attack_wave(context)
        # False again because event should have been sent last time
        assert not detector.is_attack_wave(context)


def test_non_web_scanner():
    detector = new_attack_wave_detector()
    context = test_utils.generate_context()

    # Mock is_web_scanner to return False for this test
    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=False,
    ):
        # Should return False even after multiple calls because it's not a web scanner
        for _ in range(10):
            assert not detector.is_attack_wave(context)


def test_a_web_scanner_with_delays():
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        detector = new_attack_wave_detector()
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=30 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        assert not detector.is_attack_wave(context)
        # Is true because the threshold is 6
        assert detector.is_attack_wave(context)
        # False again because event should have been sent last time
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=60 * 60 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Still false because minimum time between events is 1 hour
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=92 * 60 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Should resend event after 1 hour
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert detector.is_attack_wave(context)


def test_samples_tracking():
    """Test that samples are tracked correctly"""
    detector = new_attack_wave_detector()
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Make a few requests
        for i in range(3):
            detector.is_attack_wave(context)

        # Check that samples are being tracked (should have only 1 unique sample)
        samples = detector.get_samples_for_ip(context.remote_address)
        assert len(samples) == 1  # Only 1 unique sample despite 3 identical requests
        assert samples[0]["method"] == "POST"
        assert samples[0]["url"] == "http://localhost:8080/"

        # Make more requests to exceed the sample limit
        for i in range(10):
            detector.is_attack_wave(context)

        # Should still have only the most recent samples (limited to 10)
        samples = detector.get_samples_for_ip(context.remote_address)
        assert len(samples) <= 10


def test_clear_samples():
    """Test that samples can be cleared"""
    detector = new_attack_wave_detector()
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Make some requests
        for i in range(5):
            detector.is_attack_wave(context)

        # Verify samples exist (should have only 1 unique sample)
        samples = detector.get_samples_for_ip(context.remote_address)
        assert len(samples) == 1  # Only 1 unique sample despite 5 identical requests

        # Clear samples
        detector.clear_samples_for_ip(context.remote_address)

        # Verify samples are cleared
        samples = detector.get_samples_for_ip(context.remote_address)
        assert len(samples) == 0


def test_a_slow_web_scanner_that_triggers_in_the_second_interval():
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        detector = new_attack_wave_detector()
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=62 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert detector.is_attack_wave(context)


def test_a_slow_web_scanner_that_triggers_in_the_third_interval():
    context = test_utils.generate_context()

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        detector = new_attack_wave_detector()
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=62 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Still false because minimum time between events is 1 hour
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=124 * 1000),
    ), patch(
        "aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector.is_web_scanner",
        return_value=True,
    ):
        # Should resend event after 1 hour
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert not detector.is_attack_wave(context)
        assert detector.is_attack_wave(context)
