import time
import pytest
import json
import requests
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type

# e2e tests for flask_postgres sample app
post_url_fw = "http://localhost:8096/create"
post_url_nofw = "http://localhost:8097/create"

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], None)

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
    assert attacks[0]["attack"]["operation"] == "asyncpg.connection.Connection.execute"
    assert attacks[0]["attack"]["pathToPayload"] == '.dog_name'
    assert attacks[0]["attack"]["payload"] == "\"Dangerous Bobby', TRUE); -- \""
    assert attacks[0]["attack"]["source"] == "body"
    assert attacks[0]["attack"]["user"]["id"] == "user123"
    assert attacks[0]["attack"]["user"]["name"] == "John Doe"

def test_dangerous_response_with_form_header_but_json_body():
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    json_body = json.dumps({"dog_name": "Dangerous bobby', 1); -- "})

    res = requests.post(post_url_fw + "/json", headers=headers, data=json_body)
    assert res.status_code == 500
    time.sleep(5)

    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 2
    del attacks[1]["attack"]["stack"]
    assert attacks[1]["attack"] == {
        "blocked": True,
        "kind": "sql_injection",
        "metadata": {
            "sql": "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Dangerous bobby', 1); -- ', FALSE)"
        },
        "operation": "asyncpg.connection.Connection.execute",
        "pathToPayload": ".dog_name",
        "payload": '"Dangerous bobby\', 1); -- "',
        "source": "body",
        "user": None,
    }

def test_dangerous_response_without_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 201

