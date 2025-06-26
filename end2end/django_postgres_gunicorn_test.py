import pytest
import requests
import time
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type

# e2e tests for django_postgres_gunicorn sample app
post_url_fw = "http://localhost:8100/app/create"
post_url_nofw = "http://localhost:8101/app/create"

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], ["gunicorn", "django", "psycopg2-binary"])

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    dog_name = "Dangerous bobby', TRUE); -- "
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
            'dialect': "postgres",
            'sql': "INSERT INTO sample_app_Dogs (dog_name, is_admin) VALUES ('Dangerous bobby', TRUE); -- ', FALSE)"
        },
        'operation': "psycopg2.Connection.Cursor.execute",
        'pathToPayload': '.dog_name.[0]',
        'payload': "\"Dangerous bobby', TRUE); -- \"",
        'source': "body",
        'user': None
    }


def test_dangerous_response_with_firewall():
    dog_name = "Dangerous bobby', TRUE); -- "
    cookie_header = "dog_name=Dangerous bobby', TRUE) --; ,2=2"
    res = requests.get(f"{post_url_fw}/via_cookies", headers={
        "Cookie": cookie_header
    })
    assert res.status_code == 500

    time.sleep(5)  # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 2
    assert attacks[1]["attack"]["blocked"]
    assert attacks[1]["attack"]["kind"] == "sql_injection"
    assert attacks[1]["attack"]["metadata"] == {
        'dialect': "postgres",
        'sql': "INSERT INTO sample_app_Dogs (dog_name, is_admin) VALUES ('Dangerous bobby', TRUE) -- ', FALSE)"
    }
    assert attacks[1]["pathToPayload"] == ".dog_name"
    assert attacks[1]["source"] == "cookies"
    assert attacks[1]["payload"] == "\"Dangerous bobby', TRUE) --\""


def test_dangerous_response_without_firewall():
    dog_name = "Dangerous bobby', TRUE); -- "
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200

