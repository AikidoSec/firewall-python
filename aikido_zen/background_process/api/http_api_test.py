import weakref
from unittest.mock import Mock

import pytest
import aikido_zen.test_utils as test_utils
from aikido_zen.background_process.api.http_api import ReportingApiHTTP
from aikido_zen.background_process.api import http_api

# Sample event data for testing
sample_event = {"event_type": "test_event", "data": {"key": "value"}}


def test_report_data_401_code():
    api = ReportingApiHTTP("https://guard.aikido.dev/")

    response = api.report("wrong_token", sample_event, 5)

    assert response == {"success": False, "error": "invalid_token"}


def test_report_local_valid():
    api = ReportingApiHTTP("http://localhost:5050/")

    response = api.report("mocked_token", sample_event, 5)

    assert response == {
        "success": True,
        "blockedUserIds": [],
        "endpoints": [
            {
                "forceProtectionOff": False,
                "graphql": False,
                "method": "*",
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 2,
                    "windowSizeInMS": 5000,
                },
                "route": "/test_ratelimiting_1",
            }
        ],
        "domains": [],
        "blockNewOutgoingRequests": False,
        "receivedAnyStats": False,
    }


def test_report_local_timeout():
    api = ReportingApiHTTP("http://localhost:5050/timeout5/")

    response = api.report("mocked_token", sample_event, 4)

    assert response == {"success": False, "error": "timeout"}


def test_local_gzip():
    api = ReportingApiHTTP("http://localhost:5050/")
    response = api.fetch_firewall_lists("token")

    assert response == {
        "success": True,
        "allowedIPAddresses": [],
        "blockedIPAddresses": [
            {
                "key": "geoip/blocked",
                "description": "geo restrictions",
                "ips": ["1.2.3.4"],
                "source": "geoip",
            }
        ],
        "monitoredIPAddresses": [
            {
                "key": "tor/exit_nodes",
                "description": "Tor exit nodes",
                "ips": ["1.2.3.4", "9.9.9.9"],
                "source": "tor",
            }
        ],
        "blockedUserAgents": "",
        "monitoredUserAgents": "MonitoredTestBot",
        "userAgentDetails": [
            {"key": "monitoredtestbot", "pattern": "MonitoredTestBot"}
        ],
    }


@pytest.fixture
def mock_post(monkeypatch):
    response = Mock(status_code=200)
    response.json.return_value = {"success": True}
    post = Mock(return_value=response)
    monkeypatch.setattr(http_api.requests, "post", post)
    return post


@pytest.fixture
def reporting_api(mock_post):
    return ReportingApiHTTP(
        reporting_url="https://example.com/",
        max_events_per_interval=3,
        interval_in_ms=10000,
    )


def test_report_within_limit(reporting_api, mock_post):
    event = {"type": "detected_attack", "time": 1000}

    with test_utils.patch_time(time_s=2):
        response = reporting_api.report(token="token", event=event, timeout_in_sec=5)

    assert response == {"success": True}
    assert len(reporting_api.report_times) == 1
    mock_post.assert_called_once_with(
        "https://example.com/api/runtime/events",
        json=event,
        timeout=5,
        headers={"Authorization": "token", "Content-Type": "application/json"},
    )


def test_report_exceeds_limit(reporting_api, mock_post):
    event = {"type": "detected_attack", "time": 1000}
    reporting_api.report_times = [1000, 2000, 3000]

    with test_utils.patch_time(time_s=4):
        response = reporting_api.report(token="token", event=event, timeout_in_sec=5)

    assert response == {"success": False, "error": "max_attacks_reached"}
    assert len(reporting_api.report_times) == 3
    mock_post.assert_not_called()


def test_report_within_limit_after_expiry(reporting_api):
    reporting_api.report_times = [1000, 2001]
    event = {"type": "detected_attack", "time": 11000}

    with test_utils.patch_time(time_s=12):
        response = reporting_api.report(token="token", event=event, timeout_in_sec=5)

    assert response == {"success": True}
    assert len(reporting_api.report_times) == 2


def test_report_with_non_attack_event(reporting_api, mock_post):
    event = {"type": "other_event", "time": 1000}
    response = reporting_api.report(token="token", event=event, timeout_in_sec=5)

    assert response == {"success": True}
    assert len(reporting_api.report_times) == 0
    assert mock_post.call_args.kwargs["json"] == event


def test_report_multiple_events_within_limit(reporting_api, mock_post):
    events = [
        {"type": "detected_attack", "time": 1000},
        {"type": "detected_attack", "time": 2000},
        {"type": "detected_attack", "time": 3000},
    ]

    with test_utils.patch_time(time_s=4):
        for event in events:
            response = reporting_api.report(
                token="token", event=event, timeout_in_sec=5
            )
            assert response == {"success": True}

    assert len(reporting_api.report_times) == 3
    assert mock_post.call_count == 3


def test_report_mixed_event_types(reporting_api):
    attack_event = {"type": "detected_attack", "time": 1000}
    non_attack_event = {"type": "other_event", "time": 2000}

    assert reporting_api.report("token", attack_event, 5) == {"success": True}
    assert len(reporting_api.report_times) == 1
    assert reporting_api.report("token", non_attack_event, 5) == {"success": True}
    assert len(reporting_api.report_times) == 1


def test_report_event_expiry(reporting_api, mock_post):
    reporting_api.report_times = [1000, 2000]
    mock_post.side_effect = RuntimeError("Request failed")
    event = {"type": "detected_attack", "time": 11000}

    with test_utils.patch_time(time_s=12):
        response = reporting_api.report(token="token", event=event, timeout_in_sec=5)

    assert response == {"error": "unknown", "success": False}
    assert len(reporting_api.report_times) == 1


def test_report_event_at_boundary(reporting_api, mock_post):
    reporting_api.report_times = [1000]
    mock_post.side_effect = RuntimeError("Request failed")
    event = {"type": "detected_attack", "time": 10000}

    with test_utils.patch_time(time_s=10):
        response = reporting_api.report(token="token", event=event, timeout_in_sec=5)

    assert response == {"error": "unknown", "success": False}
    assert len(reporting_api.report_times) == 2


def test_report_invalid_event_type(reporting_api, mock_post):
    event = {"type": "invalid_event", "time": 1000}
    response = reporting_api.report(token="token", event=event, timeout_in_sec=5)

    assert response == {"success": True}
    assert len(reporting_api.report_times) == 0
    assert mock_post.call_args.kwargs["json"] == event


def test_report_no_events(reporting_api, mock_post):
    event = {"type": "detected_attack", "time": 1000}

    with test_utils.patch_time(time_s=2):
        response = reporting_api.report(token="token", event=event, timeout_in_sec=5)

    assert response == {"success": True}
    assert len(reporting_api.report_times) == 1
    assert mock_post.call_args.kwargs["json"] == event


def test_report_does_not_retain_attack_payload(reporting_api, mock_post):
    class Event(dict):
        pass

    event = Event(type="detected_attack", time=1000, request={"body": "attack"})
    event_ref = weakref.ref(event)

    with test_utils.patch_time(time_s=2):
        reporting_api.report(token="token", event=event, timeout_in_sec=5)

    assert mock_post.call_args.kwargs["json"] == event
    mock_post.reset_mock()
    del event
    assert event_ref() is None
