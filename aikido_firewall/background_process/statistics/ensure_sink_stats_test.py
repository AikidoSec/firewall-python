import pytest
from .ensure_sink_stats import ensure_sink_stats, EMPTY_STATS_OBJECT


class MockStatistics:
    def __init__(self):
        self.stats = {}


def test_ensure_sink_stats_initialization():
    statistics_obj = MockStatistics()
    sink = "example_sink"

    # Ensure the sink stats are initialized
    ensure_sink_stats(statistics_obj, sink)

    # Check if the sink stats are correctly initialized
    assert sink in statistics_obj.stats
    assert statistics_obj.stats[sink] == EMPTY_STATS_OBJECT


def test_ensure_sink_stats_already_initialized():
    statistics_obj = MockStatistics()
    sink = "example_sink"

    # Initialize the sink stats first
    ensure_sink_stats(statistics_obj, sink)

    # Ensure calling it again does not overwrite the existing stats
    ensure_sink_stats(statistics_obj, sink)

    # Check if the sink stats are still the same
    assert statistics_obj.stats[sink] == EMPTY_STATS_OBJECT


def test_ensure_sink_stats_multiple_sinks():
    statistics_obj = MockStatistics()

    # Initialize multiple sinks
    ensure_sink_stats(statistics_obj, "sink_one")
    ensure_sink_stats(statistics_obj, "sink_two")

    # Check if both sinks are initialized correctly
    assert "sink_one" in statistics_obj.stats
    assert "sink_two" in statistics_obj.stats
    assert statistics_obj.stats["sink_one"] == EMPTY_STATS_OBJECT
    assert statistics_obj.stats["sink_two"] == EMPTY_STATS_OBJECT


def test_ensure_sink_stats_empty_stats_object():
    statistics_obj = MockStatistics()
    sink = "empty_sink"

    # Ensure the sink stats are initialized
    ensure_sink_stats(statistics_obj, sink)

    # Check if the initialized stats object is empty
    assert statistics_obj.stats[sink] == EMPTY_STATS_OBJECT
