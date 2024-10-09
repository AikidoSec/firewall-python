import time
import pytest
import requests
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type, validate_heartbeat

# e2e tests for django_mysql sample app
post_url_fw = "http://localhost:8080/app/create"
post_url_nofw = "http://localhost:8081/app/create"

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], ["django", "mysqlclient"])

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 200

def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 500
    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    
    assert len(attacks) == 1
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"] == {
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {'sql': 'INSERT INTO sample_app_dogs (dog_name, dog_boss) VALUES ("Dangerous bobby", 1); -- ", "N/A")'},
        'operation': 'MySQLdb.Cursor.execute',
        'pathToPayload': '.dog_name',
        'payload': '"Dangerous bobby\\", 1); -- "',
        'source': "body",
        'user': None
    }

def test_dangerous_response_without_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200

def test_initial_heartbeat():
    time.sleep(55) # Sleep 5 + 55 seconds for heartbeat
    events = fetch_events_from_mock("http://localhost:5000")
    heartbeat_events = filter_on_event_type(events, "heartbeat")
    assert len(heartbeat_events) == 1
    validate_heartbeat(heartbeat_events[0], 
        [{
            "apispec": {},
            "hits": 1,
            "hits_delta_since_sync": 1,
            "method": "POST",
            "path": "/app/create"
        }], 
        {"aborted":0,"attacksDetected":{"blocked":1,"total":1},"total":0}
    )
