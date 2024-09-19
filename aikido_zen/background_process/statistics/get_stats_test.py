import pytest
from .get_stats import get_stats


class MockStatistics:
    def __init__(self):
        self.stats = {}
        self.started_at = None
        self.requests = 0


def test_get_stats_single_sink(monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 2
    )
    statistics_object = MockStatistics()
    statistics_object.stats = {
        "sink_one": {
            "total": 10,
            "attacksDetected": {"total": 2, "blocked": 1},
            "interceptorThrewError": 0,
            "withoutContext": 5,
            "compressedTimings": [],
        }
    }
    statistics_object.started_at = "2023-01-01T00:00:00Z"
    statistics_object.requests = 30

    expected = {
        "sinks": {
            "sink_one": {
                "total": 10,
                "attacksDetected": {"total": 2, "blocked": 1},
                "interceptorThrewError": 0,
                "withoutContext": 5,
                "compressedTimings": [],
            }
        },
        "startedAt": "2023-01-01T00:00:00Z",
        "endedAt": 2,
        "requests": 30,
    }

    assert get_stats(statistics_object) == expected


def test_get_stats_multiple_sinks(monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 5
    )
    statistics_object = MockStatistics()
    statistics_object.stats = {
        "sink_one": {
            "total": 10,
            "attacksDetected": {"total": 2, "blocked": 1},
            "interceptorThrewError": 0,
            "withoutContext": 5,
            "compressedTimings": [],
        },
        "sink_two": {
            "total": 20,
            "attacksDetected": {"total": 3, "blocked": 2},
            "interceptorThrewError": 1,
            "withoutContext": 10,
            "compressedTimings": [],
        },
    }
    statistics_object.started_at = "2023-01-01T00:00:00Z"
    statistics_object.requests = 30

    expected = {
        "sinks": {
            "sink_one": {
                "total": 10,
                "attacksDetected": {"total": 2, "blocked": 1},
                "interceptorThrewError": 0,
                "withoutContext": 5,
                "compressedTimings": [],
            },
            "sink_two": {
                "total": 20,
                "attacksDetected": {"total": 3, "blocked": 2},
                "interceptorThrewError": 1,
                "withoutContext": 10,
                "compressedTimings": [],
            },
        },
        "startedAt": "2023-01-01T00:00:00Z",
        "endedAt": 5,
        "requests": 30,
    }

    assert get_stats(statistics_object) == expected


def test_get_stats_empty_stats(monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 1
    )
    statistics_object = MockStatistics()
    statistics_object.stats = {}
    statistics_object.started_at = "2023-01-01T00:00:00Z"
    statistics_object.requests = 0

    expected = {
        "sinks": {},
        "startedAt": "2023-01-01T00:00:00Z",
        "endedAt": 1,
        "requests": 0,
    }

    assert get_stats(statistics_object) == expected


def test_get_stats_no_started_at(monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms", lambda: 10
    )
    statistics_object = MockStatistics()
    statistics_object.stats = {
        "sink_one": {
            "total": 10,
            "attacksDetected": {"total": 2, "blocked": 1},
            "interceptorThrewError": 0,
            "withoutContext": 5,
            "compressedTimings": [],
        }
    }
    statistics_object.started_at = None
    statistics_object.requests = 30

    expected = {
        "sinks": {
            "sink_one": {
                "total": 10,
                "attacksDetected": {"total": 2, "blocked": 1},
                "interceptorThrewError": 0,
                "withoutContext": 5,
                "compressedTimings": [],
            }
        },
        "startedAt": None,
        "endedAt": 10,
        "requests": 30,
    }

    assert get_stats(statistics_object) == expected


if __name__ == "__main__":
    pytest.main()
