import pytest
from unittest.mock import MagicMock
from .on_inspected_call import on_inspected_call


def test_no_context():
    """Test when without_context is True."""
    statistics_object = MagicMock()
    statistics_object.stats = {
        "sink1": {
            "total": 0,
            "withoutContext": 0,
            "durations": [],
            "attacksDetected": {"total": 0, "blocked": 0},
        }
    }
    statistics_object.max_perf_samples_in_mem = 5

    on_inspected_call(statistics_object, "sink1", 150, False, False, True)

    assert statistics_object.stats["sink1"]["total"] == 1
    assert statistics_object.stats["sink1"]["withoutContext"] == 1
    assert statistics_object.stats["sink1"]["durations"] == []


def test_with_context_and_no_attack():
    """Test when there is context and no attack detected."""
    statistics_object = MagicMock()
    statistics_object.stats = {
        "sink1": {
            "total": 0,
            "withoutContext": 0,
            "durations": [],
            "attacksDetected": {"total": 0, "blocked": 0},
        }
    }
    statistics_object.max_perf_samples_in_mem = 5

    on_inspected_call(statistics_object, "sink1", 150, False, False, False)

    assert statistics_object.stats["sink1"]["total"] == 1
    assert statistics_object.stats["sink1"]["withoutContext"] == 0
    assert statistics_object.stats["sink1"]["durations"] == [150]
    assert statistics_object.stats["sink1"]["attacksDetected"]["total"] == 0


def test_with_context_and_attack_detected():
    """Test when there is context and an attack is detected."""
    statistics_object = MagicMock()
    statistics_object.stats = {
        "sink1": {
            "total": 0,
            "withoutContext": 0,
            "durations": [],
            "attacksDetected": {"total": 0, "blocked": 0},
        }
    }
    statistics_object.max_perf_samples_in_mem = 5

    on_inspected_call(statistics_object, "sink1", 200, True, True, False)

    assert statistics_object.stats["sink1"]["total"] == 1
    assert statistics_object.stats["sink1"]["durations"] == [200]
    assert statistics_object.stats["sink1"]["attacksDetected"]["total"] == 1
    assert statistics_object.stats["sink1"]["attacksDetected"]["blocked"] == 1


def test_compress_samples_when_limit_exceeded():
    """Test when the number of durations exceeds the limit."""
    statistics_object = MagicMock()
    statistics_object.stats = {
        "sink1": {
            "total": 0,
            "withoutContext": 0,
            "durations": [100, 200, 300, 400, 500],
            "attacksDetected": {"total": 0, "blocked": 0},
        }
    }
    statistics_object.max_perf_samples_in_mem = 5

    # Mock the compress_perf_samples function to avoid actual compression
    statistics_object.compress_perf_samples = MagicMock()

    on_inspected_call(statistics_object, "sink1", 600, False, False, False)

    assert statistics_object.stats["sink1"]["durations"] == [
        100,
        200,
        300,
        400,
        500,
        600,
    ]
