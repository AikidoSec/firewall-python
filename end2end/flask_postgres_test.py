import time
import pytest
import json
import requests
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type

# e2e tests for flask_postgres sample app
post_url_fw = "http://localhost:8090/create"
post_url_nofw = "http://localhost:8091/create"
get_url_cookie_fw = "http://localhost:8090/create_with_cookie"
get_url_cookie_nofw = "http://localhost:8091/create_with_cookie"

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
        'metadata': {'sql': "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Dangerous Bobby', TRUE); -- ', FALSE)"},
        'operation': "psycopg2.Connection.Cursor.execute",
        'pathToPayload': '.dog_name',
        'payload':  '"Dangerous Bobby\', TRUE); -- "',
        'source': "body",
        'user': None
    }
    assert attacks[1]["attack"] == {
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {'sql': "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Bobby', TRUE) --', FALSE)"},
        'operation': "psycopg2.Connection.Cursor.execute",
        'pathToPayload': '.dog_name',
        'payload': "\"Bobby', TRUE) --\"",
        'source': "cookies",
        'user': None
    }
