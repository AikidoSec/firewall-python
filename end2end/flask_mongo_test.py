import json
import time
import pytest
import requests
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type

# e2e tests for flask_mysql sample app
post_url_fw = "http://localhost:8094/create"
post_url_nofw = "http://localhost:8095/create"

post_json_url_fw = "http://localhost:8094/auth"
post_json_url_nofw = "http://localhost:8095/auth"


# Create dogs:
def test_create_dog_fw():
    dog_name = "bobby_tables"
    pswd = "bobby123"
    res = requests.post(post_url_fw, data={'dog_name': dog_name, 'pswd': pswd})
    print(res.text)
    assert "created successfully" in res.text
    assert res.status_code == 200
def test_create_dog_no_fw():
    dog_name = "bobby_tables2"
    pswd = "bobby123"
    res = requests.post(post_url_nofw, data={'dog_name': dog_name, 'pswd': pswd})
    print(res.text)
    assert "created successfully" in res.text
    assert res.status_code == 200

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], ["flask", "pymongo"])

# Auth dogs with right password:
def test_safe_auth_fw():
    dog_name = "bobby_tables"
    pswd = "bobby123"
    res = requests.post(post_json_url_fw, json={'dog_name': dog_name, "pswd": pswd})
    assert res.ok
    assert res.text == "Dog with name bobby_tables authenticated successfully"
    assert res.status_code == 200
def test_safe_auth_nofw():
    dog_name = "bobby_tables"
    pswd = "bobby123"
    res = requests.post(post_json_url_nofw, json={'dog_name': dog_name, "pswd": pswd})
    assert res.ok
    assert res.text == "Dog with name bobby_tables authenticated successfully"
    assert res.status_code == 200

# Auth dogs with wrong password:
def test_safe_auth_wrong_pswd_fw():
    dog_name = "bobby_tables"
    pswd = "WrongPassword"
    res = requests.post(post_json_url_fw, json={'dog_name': dog_name, "pswd": pswd})
    assert res.ok
    assert res.text == "Auth failed"
    assert res.status_code == 200
def test_safe_auth_wrong_pswd_nofw():
    dog_name = "bobby_tables"
    pswd = "WrongPassword"
    res = requests.post(post_json_url_nofw, json={'dog_name': dog_name, "pswd": pswd})
    assert res.ok
    assert res.text == "Auth failed"
    assert res.status_code == 200

# Test NoSQL injection:
def test_dangerous_auth_fw():
    dog_name = "bobby_tables"
    pswd = { "$ne": ""}
    res = requests.post(post_json_url_fw, json={'dog_name': dog_name, "pswd": pswd})

    assert not res.ok
    assert res.status_code == 500

    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    
    assert len(attacks) == 1
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"] == {
        "blocked": True,
        "kind": "nosql_injection",
        'metadata': {'filter': '{"dog_name": "bobby_tables", "pswd": {"$ne": ""}}'},
        'operation': "pymongo.collection.Collection.find",
        'pathToPayload': ".pswd",
        'payload': '{"$ne": ""}',
        'source': "body",
        'user': None
    }

def test_dangerous_auth_nofw():
    dog_name = "bobby_tables"
    pswd = { "$ne": ""}
    res = requests.post(post_json_url_nofw, json={'dog_name': dog_name, "pswd": pswd})
    assert res.ok
    assert res.text == "Dog with name bobby_tables authenticated successfully"
    assert res.status_code == 200


def test_dangerous_auth_fw_force():
    dog_name = "bobby_tables"
    pswd = {"$ne": ""}
    json_data = json.dumps({'dog_name': dog_name, "pswd": pswd})
    res = requests.post(post_json_url_fw + "_force", data=json_data)

    assert not res.ok
    assert res.status_code == 500

    time.sleep(5)  # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 2
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"] == {
        "blocked": True,
        "kind": "nosql_injection",
        'metadata': {'filter': '{"dog_name": "bobby_tables", "pswd": {"$ne": ""}}'},
        'operation': "pymongo.collection.Collection.find",
        'pathToPayload': ".pswd",
        'payload': '{"$ne": ""}',
        'source': "body",
        'user': None
    }


# --- AIKIDO-5RDTZW1V regression: invalid UTF-8 bytes must not bypass detection ---

def test_bypass_invalid_utf8_bytes_path_traversal():
    # An attacker prepends \xff (invalid UTF-8) to a path traversal payload.
    # Before the fix, decode("utf-8") raised UnicodeDecodeError and the body was
    # never stored, so the firewall saw nothing.  After the fix the body is decoded
    # with errors="replace" and the traversal is still detected.
    body = b"\xff/../../../../../etc/passwd"
    res = requests.post("http://localhost:8094/read", data=body)
    assert res.status_code == 500

    time.sleep(5)
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 3
    assert attacks[2]["attack"]["kind"] == "path_traversal"
    assert attacks[2]["attack"]["blocked"] is True
    assert attacks[2]["attack"]["source"] == "body"


# --- AIKIDO-B3YABOSP regression: surrogate bytes in JSON must not bypass detection ---

def test_bypass_surrogate_bytes_nosql_injection():
    # Surrogate bytes (\xed\xa0\x80) make decode("utf-8") raise, so the old code
    # never parsed the JSON and the NoSQL injection payload {"$ne":""} was invisible.
    # After the fix, json.loads(bytes) is tried first (it uses surrogatepass internally)
    # so the dict body is fully parsed and the injection is caught.
    body = b'{"dog_name": "bobby_tables", "pswd": {"$ne": ""}, "bypass": "\xed\xa0\x80"}'
    res = requests.post("http://localhost:8094/auth-raw", data=body)
    assert res.status_code == 500

    time.sleep(5)
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 4
    assert attacks[3]["attack"]["kind"] == "nosql_injection"
    assert attacks[3]["attack"]["blocked"] is True
    assert attacks[3]["attack"]["source"] == "body"
