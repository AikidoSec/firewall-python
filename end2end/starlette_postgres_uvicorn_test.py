import time
import pytest
import http.client
import requests
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type

# e2e tests for flask_postgres sample app
post_url_fw = "http://localhost:8102/create"
post_url_nofw = "http://localhost:8103/create"
sync_route_fw = "http://localhost:8102/sync_route"
sync_route_nofw = "http://localhost:8103/sync_route"

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], None) # Don't assert stack

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 201

def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 201


def test_dangerous_response_with_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 500
    
    time.sleep(5) # Wait for attack to be reported
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

    assert attacks[0]["request"]["source"] == "starlette"
    assert attacks[0]["request"]["route"] == "/create"
    assert attacks[0]["request"]["userAgent"] == "python-requests/2.32.3"


def test_dangerous_response_without_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 201


def test_dangerous_response_with_firewall_via_headers():
    conn = http.client.HTTPConnection("localhost", 8102)
    conn.putrequest("GET", "/create_dog_from_headers")
    conn.putheader("X-Dog-Name", "Dangerous Bobby', TRUE); --")
    conn.putheader("X-Dog-Name", "safe dog name")
    conn.endheaders()
    res = conn.getresponse()
    assert res.status == 500
    conn.close()

    time.sleep(5)

    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 2
    del attacks[0]
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"]["blocked"] == True
    assert attacks[0]["attack"]["kind"] == "sql_injection"
    assert attacks[0]["attack"]["metadata"][
               "sql"] == "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Dangerous Bobby', TRUE); --', FALSE)"
    assert attacks[0]["attack"]["metadata"]["dialect"] == "postgres"
    assert attacks[0]["attack"]["operation"] == "asyncpg.connection.Connection.execute"
    assert attacks[0]["attack"]["pathToPayload"] == ".X_DOG_NAME.[0]"
    assert attacks[0]["attack"]["payload"] == "\"Dangerous Bobby', TRUE); --\""
    assert attacks[0]["attack"]["source"] == "headers"
    assert attacks[0]["attack"]["user"]["id"] == "user123"
    assert attacks[0]["attack"]["user"]["name"] == "John Doe"

    assert attacks[0]["request"]["source"] == "starlette"
    assert attacks[0]["request"]["route"] == "/create_dog_from_headers"


def test_sync_route_with_firewall():
    res = requests.get(sync_route_fw)
    assert res.status_code == 200

def test_sync_route_without_firewall():
    res = requests.get(sync_route_nofw)
    assert res.status_code == 200
