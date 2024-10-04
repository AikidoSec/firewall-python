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
