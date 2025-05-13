import time
import pytest
import requests
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type

# e2e tests for flask_postgres sample app
post_url_fw = "http://localhost:8092/xml_post_lxml"
post_url_nofw = "http://localhost:8093/xml_post_lxml"

def test_safe_response_with_firewall():
    xml_data = '<dogs><dog dog_name="Bobby" /></dogs>'
    res = requests.post(post_url_fw, data=xml_data)
    assert res.status_code == 200

def test_safe_response_without_firewall():
    xml_data = '<dogs><dog dog_name="Bobby" /></dogs>'
    res = requests.post(post_url_nofw, data=xml_data)
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    xml_data = '<dogs><dog dog_name="Malicious dog\', TRUE); -- " /></dogs>'
    res = requests.post(post_url_fw, data=xml_data)
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
            'sql': "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Malicious dog', TRUE); -- ', FALSE)"
        },
        'operation': "psycopg2.Connection.Cursor.execute",
        'pathToPayload': ".dog_name.[0]",
        'payload': "\"Malicious dog', TRUE); -- \"",
        'source': "xml",
        'user': None
    }

def test_dangerous_response_without_firewall():
    xml_data = '<dogs><dog dog_name="Malicious dog\', TRUE); -- " /></dogs>'
    res = requests.post(post_url_nofw, data=xml_data)
    assert res.status_code == 200

