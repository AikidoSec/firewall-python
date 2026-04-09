import time
import pytest
import requests
from .server.check_events_from_mock import (
    fetch_events_from_mock,
    validate_started_event,
    validate_heartbeat,
    filter_on_event_type,
)

post_url_fw = "http://localhost:8118/create"
post_url_nofw = "http://localhost:8119/create"
sync_route_fw = "http://localhost:8118/sync_route"
sync_route_nofw = "http://localhost:8119/sync_route"


def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], None)


def test_safe_response_with_firewall():
    res = requests.post(post_url_fw, data={"dog_name": "Bobby Tables"})
    assert res.status_code == 201


def test_safe_response_without_firewall():
    res = requests.post(post_url_nofw, data={"dog_name": "Bobby Tables"})
    assert res.status_code == 201


def test_dangerous_response_with_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_fw, data={"dog_name": dog_name})
    assert res.status_code == 500

    time.sleep(5)  # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 1
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"]["blocked"] == True
    assert attacks[0]["attack"]["kind"] == "sql_injection"
    assert attacks[0]["attack"]["metadata"]["sql"] == "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Dangerous Bobby', TRUE); -- ', FALSE)"
    assert attacks[0]["attack"]["metadata"]["dialect"] == "postgres"
    assert attacks[0]["attack"]["operation"] == "asyncpg.connection.Connection.execute"
    assert attacks[0]["attack"]["pathToPayload"] == ".dog_name"
    assert attacks[0]["attack"]["payload"] == "\"Dangerous Bobby', TRUE); -- \""
    assert attacks[0]["attack"]["source"] == "body"
    assert attacks[0]["attack"]["user"]["id"] == "user123"
    assert attacks[0]["attack"]["user"]["name"] == "John Doe"

    # These assertions verify the pre/post response hooks fired for FastAPI APIRoute endpoints.
    # Without patching fastapi.routing.request_response, route will be None/empty and
    # source will not reflect the fastapi framework context.
    assert attacks[0]["request"]["route"] == "/create"
    assert attacks[0]["request"]["userAgent"] == "python-requests/2.32.3"


def test_dangerous_response_without_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_nofw, data={"dog_name": dog_name})
    assert res.status_code == 201


def test_sync_route_with_firewall():
    res = requests.get(sync_route_fw)
    assert res.status_code == 200


def test_sync_route_without_firewall():
    res = requests.get(sync_route_nofw)
    assert res.status_code == 200


def test_routes_discovered_in_heartbeat():
    # This test verifies that FastAPI APIRoute endpoints are discovered via route discovery.
    # Without patching fastapi.routing.request_response, the heartbeat will report
    # current_routes: {} even with active traffic, because the post_response hook never fires.
    time.sleep(55)  # Wait for first heartbeat (fires ~60s after start)

    events = fetch_events_from_mock("http://localhost:5000")
    heartbeat_events = filter_on_event_type(events, "heartbeat")
    assert len(heartbeat_events) >= 1

    routes = heartbeat_events[0]["routes"]
    route_map = {(r["method"], r["path"]): r for r in routes}

    assert ("POST", "/create") in route_map
    create_route = route_map[("POST", "/create")]
    assert create_route["apispec"] == {
        "auth": None,
        "body": {
            "schema": {
                "properties": {"dog_name": {"type": "string"}},
                "type": "object",
            },
            "type": "form-urlencoded",
        },
        "query": None,
    }
    assert create_route["hits"] == 1

    assert ("GET", "/sync_route") in route_map
