import pytest
import requests
import time
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type

# e2e tests for django_mysql_gunicorn sample app
post_url_fw = "http://localhost:8082/app/create/"
post_url_nofw = "http://localhost:8083/app/create/"

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], ["gunicorn", "django"])

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
        'metadata': {
            'dialect': 'mysql',
            'sql': 'INSERT INTO sample_app_dogs (dog_name, dog_boss) VALUES ("Dangerous bobby", 1); -- ", "N/A")'
        },
        'operation': 'MySQLdb.Cursor.execute',
        'pathToPayload': '.dog_name.[0]',
        'payload': '"Dangerous bobby\\", 1); -- "',
        'source': "body",
        'user': None
    }

    assert attacks[0]["request"]["source"] == "django"
    assert attacks[0]["request"]["route"] == "/app/create"
    assert attacks[0]["request"]["userAgent"] == "python-requests/2.32.3"

def test_dangerous_response_without_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200

