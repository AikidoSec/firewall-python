import pytest
from aikido_zen.background_process.api.http_api import ReportingApiHTTP

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
            {"description": "geo restrictions", "ips": ["1.2.3.4"], "source": "geoip"}
        ],
        "blockedUserAgents": "",
    }
