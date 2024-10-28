import pytest
import requests
import time
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type
# e2e tests for flask_mysql sample app
post_url_fw = "http://localhost:8086/create"
post_url_nofw = "http://localhost:8087/create"

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], ["flask", "pymysql"])

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    events = fetch_events_from_mock("http://localhost:5000")
    assert len(filter_on_event_type(events, "detected_attack")) == 0
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 500

    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    
    assert len(attacks) == 1
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"]["blocked"] == True
    assert attacks[0]["attack"]["kind"] == "sql_injection"
    assert attacks[0]["attack"]["metadata"]["sql"] == 'INSERT INTO dogs (dog_name, isAdmin) VALUES ("Dangerous bobby", 1); -- ", 0)'
    assert attacks[0]["attack"]["operation"] == 'pymysql.Cursor.execute'
    assert attacks[0]["attack"]["pathToPayload"] == '.dog_name'
    assert attacks[0]["attack"]["payload"] == '"Dangerous bobby\\", 1); -- "'
    assert attacks[0]["attack"]["source"] == "body"
    assert attacks[0]["attack"]["user"]["id"] == "123"
    assert attacks[0]["attack"]["user"]["name"] == "John Doe"



def test_dangerous_response_without_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200

