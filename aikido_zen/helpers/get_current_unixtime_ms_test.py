import pytest
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
import time


def test_get_unixtime_ms(monkeypatch):
    # Mock time.time to return a specific timestamp
    monkeypatch.setattr(
        time, "time", lambda: 1633072800.123
    )  # Example timestamp in seconds

    # Calculate the expected result in milliseconds
    expected_result = int(1633072800.123 * 1000)

    assert get_unixtime_ms() == expected_result


def test_get_unixtime_ms_zero(monkeypatch):
    # Mock time.time to return zero
    monkeypatch.setattr(time, "time", lambda: 0.0)

    # The expected result should be 0 milliseconds
    assert get_unixtime_ms() == 0
