import pytest
from unittest.mock import patch
from aikido_zen.background_process.api.http_api import ReportingApiHTTP
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from .http_api_ratelimited import ReportingApiHTTPRatelimited


@pytest.fixture
def reporting_api():
    """Fixture to create an instance of ReportingApiHTTPRatelimited."""
    return ReportingApiHTTPRatelimited(
        reporting_url="http://example.com",
        max_events_per_interval=3,
        interval_in_ms=10000,
    )


def test_report_within_limit(reporting_api):
    """Test reporting within the rate limit."""
    event = {"type": "detected_attack", "time": 1000}

    with patch.object(
        ReportingApiHTTP, "report", return_value={"success": True}
    ) as mock_report:
        with patch(
            "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
            return_value=2000,
        ):
            response = reporting_api.report(
                token="token", event=event, timeout_in_sec=5
            )
            assert response == {"success": True}
            assert len(reporting_api.events) == 1
            mock_report.assert_called_once_with("token", event, 5)


def test_report_exceeds_limit(reporting_api):
    """Test reporting when the limit is exceeded."""
    event = {"type": "detected_attack", "time": 1000}

    # Simulate adding events to reach the limit
    reporting_api.events = [
        {"type": "detected_attack", "time": 1000},
        {"type": "detected_attack", "time": 2000},
        {"type": "detected_attack", "time": 3000},
    ]

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        return_value=4000,
    ):
        response = reporting_api.report(token="token", event=event, timeout_in_sec=5)
        assert response == {"success": False, "error": "max_attacks_reached"}
        assert len(reporting_api.events) == 3  # Should not add the new event


def test_report_within_limit_after_expiry(reporting_api):
    """Test reporting after some events have expired."""
    event1 = {"type": "detected_attack", "time": 1000}
    event2 = {"type": "detected_attack", "time": 2001}

    # Add events to the list
    reporting_api.events = [event1, event2]

    with patch.object(
        ReportingApiHTTP, "report", return_value={"success": True}
    ) as mock_report:
        with patch(
            "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
            return_value=12000,
        ):
            event3 = {"type": "detected_attack", "time": 11000}
            response = reporting_api.report(
                token="token", event=event3, timeout_in_sec=5
            )
            assert response == {"success": True}
            assert (
                len(reporting_api.events) == 2
            )  # One event should have expired, and the new one is added


def test_report_with_non_attack_event(reporting_api):
    """Test reporting with a non-attack event."""
    event = {"type": "other_event", "time": 1000}

    with patch.object(
        ReportingApiHTTP, "report", return_value={"success": True}
    ) as mock_report:
        response = reporting_api.report(token="token", event=event, timeout_in_sec=5)
        assert response == {"success": True}
        assert len(reporting_api.events) == 0  # Non-attack events should not be stored
        mock_report.assert_called_once_with("token", event, 5)


def test_report_multiple_events_within_limit(reporting_api):
    """Test reporting multiple events within the rate limit."""
    events = [
        {"type": "detected_attack", "time": 1000},
        {"type": "detected_attack", "time": 2000},
        {"type": "detected_attack", "time": 3000},
    ]

    with patch.object(
        ReportingApiHTTP, "report", return_value={"success": True}
    ) as mock_report:
        with patch(
            "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
            return_value=4000,
        ):
            for event in events:
                response = reporting_api.report(
                    token="token", event=event, timeout_in_sec=5
                )
                assert response == {"success": True}
            assert len(reporting_api.events) == 3
            assert mock_report.call_count == 3


def test_report_mixed_event_types(reporting_api):
    """Test reporting with a mix of attack and non-attack events."""
    attack_event = {"type": "detected_attack", "time": 1000}
    non_attack_event = {"type": "other_event", "time": 2000}

    with patch.object(
        ReportingApiHTTP, "report", return_value={"success": True}
    ) as mock_report:
        response = reporting_api.report(
            token="token", event=attack_event, timeout_in_sec=5
        )
        assert response == {"success": True}
        assert len(reporting_api.events) == 1

        response = reporting_api.report(
            token="token", event=non_attack_event, timeout_in_sec=5
        )
        assert response == {"success": True}
        assert len(reporting_api.events) == 1  # Non-attack event should not be stored


def test_report_event_expiry(reporting_api):
    """Test that events expire correctly based on the time interval."""
    event1 = {"type": "detected_attack", "time": 1000}
    event2 = {"type": "detected_attack", "time": 2000}
    reporting_api.events = [event1, event2]

    # Simulate time passing
    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        return_value=12000,
    ):
        event3 = {"type": "detected_attack", "time": 11000}
        response = reporting_api.report(token="token", event=event3, timeout_in_sec=5)
        assert response == {"error": "timeout", "success": False}
        assert (
            len(reporting_api.events) == 1
        )  # One event should have expired, and the new one is added


def test_report_event_at_boundary(reporting_api):
    """Test reporting an event at the boundary of the interval."""
    event1 = {"type": "detected_attack", "time": 1000}
    reporting_api.events = [event1]

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        return_value=10000,
    ):
        event2 = {"type": "detected_attack", "time": 10000}  # Exactly at the boundary
        response = reporting_api.report(token="token", event=event2, timeout_in_sec=5)
        assert response == {"error": "timeout", "success": False}
        assert (
            len(reporting_api.events) == 2
        )  # Should be added since it's at the boundary


def test_report_invalid_event_type(reporting_api):
    """Test reporting with an invalid event type."""
    event = {"type": "invalid_event", "time": 1000}

    with patch.object(
        ReportingApiHTTP, "report", return_value={"success": True}
    ) as mock_report:
        response = reporting_api.report(token="token", event=event, timeout_in_sec=5)
        assert response == {"success": True}
        assert (
            len(reporting_api.events) == 0
        )  # Invalid event types should not be stored
        mock_report.assert_called_once_with("token", event, 5)


def test_report_no_events(reporting_api):
    """Test reporting when no events have been reported yet."""
    event = {"type": "detected_attack", "time": 1000}

    with patch.object(
        ReportingApiHTTP, "report", return_value={"success": True}
    ) as mock_report:
        with patch(
            "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
            return_value=2000,
        ):
            response = reporting_api.report(
                token="token", event=event, timeout_in_sec=5
            )
            assert response == {"success": True}
            assert len(reporting_api.events) == 1  # Should add the first event
            mock_report.assert_called_once_with("token", event, 5)
