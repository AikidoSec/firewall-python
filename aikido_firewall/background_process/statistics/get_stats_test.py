import pytest
from .get_stats import get_stats


class MockStatistics:
    def __init__(self):
        self.stats = {}
        self.started_at = None
        self.requests = 0


def test_get_stats_single_sink():
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
        "requests": 30,
    }

    assert get_stats(statistics_object) == expected


def test_get_stats_multiple_sinks():
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
        "requests": 30,
    }

    assert get_stats(statistics_object) == expected


def test_get_stats_empty_stats():
    statistics_object = MockStatistics()
    statistics_object.stats = {}
    statistics_object.started_at = "2023-01-01T00:00:00Z"
    statistics_object.requests = 0

    expected = {
        "sinks": {},
        "startedAt": "2023-01-01T00:00:00Z",
        "requests": 0,
    }

    assert get_stats(statistics_object) == expected


def test_get_stats_no_started_at():
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
        "requests": 30,
    }

    assert get_stats(statistics_object) == expected


if __name__ == "__main__":
    pytest.main()
