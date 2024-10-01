import pytest
from unittest.mock import MagicMock
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from . import Statistics


@pytest.fixture
def stats():
    """Fixture to create a new instance of Statistics."""
    return Statistics(max_perf_samples_in_mem=50, max_compressed_stats_in_mem=5)


def test_it_resets_stats(stats, monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 2
    )
    stats.on_inspected_call(
        without_context=False,
        sink="mongodb",
        blocked=False,
        duration_in_ms=0.1,
        attack_detected=False,
    )
    started_at = stats.get_stats()["startedAt"]

    assert stats.get_stats() == {
        "sinks": {
            "mongodb": {
                "attacksDetected": {
                    "total": 0,
                    "blocked": 0,
                },
                "interceptorThrewError": 0,
                "withoutContext": 0,
                "total": 1,
                "compressedTimings": [],
            },
        },
        "startedAt": started_at,
        "endedAt": 2,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }

    stats.reset()
    started_at = stats.get_stats()["startedAt"]

    assert stats.get_stats() == {
        "sinks": {},
        "startedAt": started_at,  # Assuming reset sets this to the current time
        "endedAt": 2,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }


def test_it_keeps_track_of_amount_of_calls(stats, monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 2
    )
    started_at = stats.get_stats()["startedAt"]
    assert stats.get_stats() == {
        "sinks": {},
        "startedAt": started_at,
        "endedAt": 2,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }

    stats.on_inspected_call(
        without_context=False,
        sink="mongodb",
        blocked=False,
        duration_in_ms=0.1,
        attack_detected=False,
    )

    assert stats.get_stats() == {
        "sinks": {
            "mongodb": {
                "attacksDetected": {
                    "total": 0,
                    "blocked": 0,
                },
                "interceptorThrewError": 0,
                "withoutContext": 0,
                "total": 1,
                "compressedTimings": [],
            },
        },
        "startedAt": started_at,
        "endedAt": 2,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }

    stats.on_inspected_call(
        without_context=True,
        sink="mongodb",
        blocked=False,
        duration_in_ms=0.1,
        attack_detected=False,
    )

    assert stats.get_stats() == {
        "sinks": {
            "mongodb": {
                "attacksDetected": {
                    "total": 0,
                    "blocked": 0,
                },
                "interceptorThrewError": 0,
                "withoutContext": 1,
                "total": 2,
                "compressedTimings": [],
            },
        },
        "startedAt": started_at,
        "endedAt": 2,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }

    stats.interceptor_threw_error("mongodb")

    assert stats.get_stats() == {
        "sinks": {
            "mongodb": {
                "attacksDetected": {
                    "total": 0,
                    "blocked": 0,
                },
                "interceptorThrewError": 1,
                "withoutContext": 1,
                "total": 3,
                "compressedTimings": [],
            },
        },
        "startedAt": started_at,
        "endedAt": 2,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }

    stats.on_inspected_call(
        without_context=False,
        sink="mongodb",
        blocked=False,
        duration_in_ms=0.1,
        attack_detected=True,
    )

    assert stats.get_stats() == {
        "sinks": {
            "mongodb": {
                "attacksDetected": {
                    "total": 1,
                    "blocked": 0,
                },
                "interceptorThrewError": 1,
                "withoutContext": 1,
                "total": 4,
                "compressedTimings": [],
            },
        },
        "startedAt": started_at,
        "endedAt": 2,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }

    stats.on_inspected_call(
        without_context=False,
        sink="mongodb",
        blocked=True,
        duration_in_ms=0.3,
        attack_detected=True,
    )

    assert stats.get_stats() == {
        "sinks": {
            "mongodb": {
                "attacksDetected": {
                    "total": 2,
                    "blocked": 1,
                },
                "interceptorThrewError": 1,
                "withoutContext": 1,
                "total": 5,
                "compressedTimings": [],
            },
        },
        "startedAt": started_at,
        "endedAt": 2,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }

    assert stats.has_compressed_stats() is False

    for i in range(50):
        stats.on_inspected_call(
            without_context=False,
            sink="mongodb",
            blocked=False,
            duration_in_ms=i * 0.1,
            attack_detected=False,
        )

    assert stats.has_compressed_stats() is True

    # Check the compressed timings
    assert len(stats.get_stats()["sinks"]["mongodb"]["compressedTimings"]) == 1


def test_it_keeps_track_of_requests(stats, monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 9
    )
    started_at = stats.get_stats()["startedAt"]

    assert stats.get_stats() == {
        "sinks": {},
        "startedAt": started_at,
        "endedAt": 9,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }

    stats.requests["total"] += 1

    assert stats.get_stats() == {
        "sinks": {},
        "startedAt": started_at,
        "endedAt": 9,
        "requests": {
            "total": 1,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }

    stats.requests["total"] += 1
    stats.on_detected_attack(blocked=False)

    assert stats.get_stats() == {
        "sinks": {},
        "startedAt": started_at,
        "endedAt": 9,
        "requests": {
            "total": 2,
            "aborted": 0,
            "attacksDetected": {
                "total": 1,
                "blocked": 0,
            },
        },
    }

    stats.requests["total"] += 1
    stats.on_detected_attack(blocked=True)

    assert stats.get_stats() == {
        "sinks": {},
        "startedAt": started_at,
        "endedAt": 9,
        "requests": {
            "total": 3,
            "aborted": 0,
            "attacksDetected": {
                "total": 2,
                "blocked": 1,
            },
        },
    }

    stats.reset()
    started_at = stats.get_stats()["startedAt"]

    assert stats.get_stats() == {
        "sinks": {},
        "startedAt": started_at,  # Assuming reset sets this to the current time
        "endedAt": 9,
        "requests": {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }


def test_it_force_compresses_stats(stats):
    stats.requests["total"] += 1

    stats.on_inspected_call(
        without_context=False,
        sink="mongodb",
        blocked=False,
        duration_in_ms=0.1,
        attack_detected=False,
    )

    assert stats.has_compressed_stats() is False

    stats.force_compress()

    assert stats.has_compressed_stats() is True


def test_it_keeps_track_of_aborted_requests(stats, monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 5
    )
    stats.requests["aborted"] += 1
    started_at = stats.get_stats()["startedAt"]

    assert stats.get_stats() == {
        "sinks": {},
        "startedAt": started_at,
        "endedAt": 5,
        "requests": {
            "total": 0,
            "aborted": 1,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        },
    }


def test_is_empty_when_stats_are_empty(stats):
    assert stats.is_empty() is True


def test_is_empty_when_requests_are_empty(stats):
    stats.requests["total"] = 0
    stats.requests["attacksDetected"]["total"] = 0
    stats.stats = {}  # Assuming stats is a dictionary
    assert stats.is_empty() is True


def test_is_empty_when_requests_have_data(stats):
    stats.requests["total"] = 1
    stats.requests["attacksDetected"]["total"] = 0
    stats.stats = {}
    assert stats.is_empty() is False


def test_is_empty_when_attacks_detected(stats):
    stats.requests["total"] = 0
    stats.requests["attacksDetected"]["total"] = 1
    stats.stats = {}
    assert stats.is_empty() is False


def test_is_empty_when_stats_have_data(stats):
    stats.requests["total"] = 0
    stats.requests["attacksDetected"]["total"] = 0
    stats.stats = {"some_stat": 1}  # Adding some data to stats
    assert stats.is_empty() is False


def test_is_empty_when_all_data_present(stats):
    stats.requests["total"] = 1
    stats.requests["attacksDetected"]["total"] = 1
    stats.stats = {"some_stat": 1}
    assert stats.is_empty() is False
