import pytest
from unittest.mock import patch
from .attack_wave_detector import AttackWaveDetector


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


def test_no_ip_address():
    detector = new_attack_wave_detector()
    assert not detector.is_attack_wave(None)


def test_a_web_scanner():
    detector = new_attack_wave_detector()
    assert not detector.is_attack_wave("::1")
    assert not detector.is_attack_wave("::1")
    assert not detector.is_attack_wave("::1")
    assert not detector.is_attack_wave("::1")
    assert not detector.is_attack_wave("::1")
    # Is true because the threshold is 6
    assert detector.is_attack_wave("::1")
    # False again because event should have been sent last time
    assert not detector.is_attack_wave("::1")


def test_a_web_scanner_with_delays():
    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ):
        detector = new_attack_wave_detector()
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=30 * 1000),
    ):
        assert not detector.is_attack_wave("::1")
        # Is true because the threshold is 6
        assert detector.is_attack_wave("::1")
        # False again because event should have been sent last time
        assert not detector.is_attack_wave("::1")

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=60 * 60 * 1000),
    ):
        # Still false because minimum time between events is 1 hour
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=92 * 60 * 1000),
    ):
        # Should resend event after 1 hour
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert detector.is_attack_wave("::1")


def test_a_slow_web_scanner_that_triggers_in_the_second_interval():
    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ):
        detector = new_attack_wave_detector()
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=62 * 1000),
    ):
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert detector.is_attack_wave("::1")


def test_a_slow_web_scanner_that_triggers_in_the_third_interval():
    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ):
        detector = new_attack_wave_detector()
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=62 * 1000),
    ):
        # Still false because minimum time between events is 1 hour
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=124 * 1000),
    ):
        # Should resend event after 1 hour
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert not detector.is_attack_wave("::1")
        assert detector.is_attack_wave("::1")
