import pytest
import requests
import time
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type
# e2e tests for flask_mysql sample app
base_url_fw = "http://localhost:8086"
base_url_nofw = "http://localhost:8087"

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], ["flask", "pymysql"])

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(base_url_fw + "/create", data={'dog_name': dog_name})
    assert res.status_code == 200


def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(base_url_nofw + "/create", data={'dog_name': dog_name})
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    events = fetch_events_from_mock("http://localhost:5000")
    assert len(filter_on_event_type(events, "detected_attack")) == 0
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(base_url_fw + "/create", data={'dog_name': dog_name})
    assert res.status_code == 500

    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    
    assert len(attacks) == 1
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"] == {
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {'sql': 'INSERT INTO dogs (dog_name, isAdmin) VALUES ("Dangerous bobby", 1); -- ", 0)'},
        'operation': 'pymysql.Cursor.execute',
        'pathToPayload': '.dog_name',
        'payload': '"Dangerous bobby\\", 1); -- "',
        'source': "body",
        'user': None
    }

def test_dangerous_response_with_firewall_route_params():
    events = fetch_events_from_mock("http://localhost:5000")
    assert len(filter_on_event_type(events, "detected_attack")) == 1
    res = requests.get(base_url_fw + "/shell/ls -la")
    assert res.status_code == 500

    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    
    assert len(attacks) == 2
    del attacks[0]
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"] == {
        "blocked": True,
        "kind": "shell_injection",
        'metadata': {'command': 'ls -la'},
        'operation': 'subprocess.Popen',
        'pathToPayload': '.command',
        'payload': '"ls -la"',
        'source': "route_params",
        'user': None
    }


def test_dangerous_response_without_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(base_url_nofw + "/create", data={'dog_name': dog_name})
    assert res.status_code == 200

