import pytest
from unittest.mock import MagicMock
from aikido_zen.helpers.percentiles import percentiles
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from .compress_perf_samples import compress_perf_samples


def test_no_durations():
    """Test when there are no durations."""
    statistics_object = MagicMock()
    statistics_object.stats = {"sink1": {"durations": [], "compressedTimings": []}}
    compress_perf_samples(statistics_object, "sink1")
    assert statistics_object.stats["sink1"]["compressedTimings"] == []
    print("test_no_durations passed")


def test_clear_durations_after_compression():
    """Test that durations are cleared after compression."""
    statistics_object = MagicMock()
    statistics_object.stats = {
        "sink1": {"durations": [100, 200, 300], "compressedTimings": []}
    }
    statistics_object.max_compressed_stats_in_mem = 5

    # Mock the percentiles function
    percentiles.return_value = (200, 300, 400, 450, 490)

    # Mock the get_unixtime_ms function
    get_unixtime_ms.return_value = 1234567890

    compress_perf_samples(statistics_object, "sink1")

    assert (
        statistics_object.stats["sink1"]["durations"] == []
    )  # Durations should be cleared
    print("test_clear_durations_after_compression passed")
