import time
import pytest
import json
import requests
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type, \
    clear_events_from_mock

# e2e tests for flask_postgres sample app
post_url_fw = "http://localhost:8090/create"
post_url_nofw = "http://localhost:8091/create"
get_url_cookie_fw = "http://localhost:8090/create_with_cookie"
get_url_cookie_nofw = "http://localhost:8091/create_with_cookie"
track_url_fw = "http://localhost:8090/track_event"
track_url_nofw = "http://localhost:8091/track_event"

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], ["flask", "psycopg2-binary"])

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 500

def test_dangerous_response_without_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_safe_cookie_creation_with_firewall():
    cookies = {
        "dog_name": "Bobby Tables",
        "corrupt_data": ";;;;;;;;;;;;;"
    }
    res = requests.get(get_url_cookie_fw, cookies=cookies)
    assert res.status_code == 200

def test_safe_cookie_creation_without_firewall():
    cookies = {
        "dog_name": "Bobby Tables",
        "corrupt_data": ";;;;;;;;;;;;;"

    }
    res = requests.get(get_url_cookie_nofw, cookies=cookies)
    assert res.status_code == 200


def test_dangerous_cookie_creation_with_firewall():
    cookies = {
        "dog_name": "Bobby', TRUE) -- ",
        "corrupt_data": ";;;;;;;;;;;;;"
    }
    res = requests.get(get_url_cookie_fw, cookies=cookies)
    assert res.status_code == 500

def test_dangerous_cookie_creation_without_firewall():
    cookies = {
        "dog_name": "Bobby', TRUE) -- ",
        "corrupt_data": ";;;;;;;;;;;;;"
    }
    res = requests.get(get_url_cookie_nofw, cookies=cookies)
    assert res.status_code == 200

def test_attacks_detected():
    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    
    assert len(attacks) == 2
    del attacks[0]["attack"]["stack"]
    del attacks[1]["attack"]["stack"]

    assert attacks[0]["attack"] == {
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {
            'dialect': "postgres",
            'sql': "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Dangerous Bobby', TRUE); -- ', FALSE)"
        },
        'operation': "psycopg2.Connection.Cursor.execute",
        'pathToPayload': '.dog_name',
        'payload':  '"Dangerous Bobby\', TRUE); -- "',
        'source': "body",
        'user': None
    }
    assert attacks[1]["attack"] == {
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {
            'dialect': "postgres",
            'sql': "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Bobby', TRUE) --', FALSE)"
        },
        'operation': "psycopg2.Connection.Cursor.execute",
        'pathToPayload': '.dog_name',
        'payload': "\"Bobby', TRUE) --\"",
        'source': "cookies",
        'user': None
    }


def test_track_sends_a_custom_event_with_firewall():
    clear_events_from_mock("http://localhost:5000")
    res = requests.get(track_url_fw, headers={"User-Agent": "e2e-test"})
    assert res.status_code == 200

    time.sleep(5)  # Wait for the event to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    custom_events = filter_on_event_type(events, "custom")

    assert len(custom_events) == 1
    assert custom_events[0]["name"] == "user.login_failed"
    assert "user" not in custom_events[0]
    assert custom_events[0]["request"] == {
        "method": "GET",
        "ipAddress": "127.0.0.1",
        "userAgent": "e2e-test",
        "source": "flask",
        "route": "/track_event",
    }
    # The custom event schema has no url, unlike a detected attack event
    assert "url" not in custom_events[0]["request"]


def test_track_sends_no_event_without_firewall():
    clear_events_from_mock("http://localhost:5000")
    res = requests.get(track_url_nofw, headers={"User-Agent": "e2e-test"})
    assert res.status_code == 200

    time.sleep(5)  # Wait, in case an event would be reported
    events = fetch_events_from_mock("http://localhost:5000")
    assert filter_on_event_type(events, "custom") == []


def test_every_event_carries_the_agent_headers():
    clear_events_from_mock("http://localhost:5000")
    res = requests.get(track_url_fw, headers={"User-Agent": "e2e-test"})
    assert res.status_code == 200

    time.sleep(5)  # Wait for the event to be reported
    captured = fetch_events_from_mock("http://localhost:5000", include_headers=True)

    assert len(captured) > 0
    for entry in captured:
        headers = entry["requestHeaders"]
        assert headers["x-agent-platform"] == "python"
        assert headers["x-agent-library"] == "firewall-python"
        assert headers["x-agent-version"] == "1.0-REPLACE-VERSION"
        assert headers["x-agent-hostname"]
        assert headers["x-agent-ip-address"]

    session_ids = {entry["requestHeaders"]["x-agent-session-id"] for entry in captured}
    assert len(session_ids) == 1
    assert session_ids.pop()
