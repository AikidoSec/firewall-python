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
    assert attacks[0]["attack"]["blocked"] == True
    assert attacks[0]["attack"]["kind"] == "sql_injection"
    assert attacks[0]["attack"]["metadata"]["sql"] == 'INSERT INTO dogs (dog_name, isAdmin) VALUES ("Dangerous bobby", 1); -- ", 0)'
    assert attacks[0]["attack"]["metadata"]["dialect"] == 'mysql'
    assert attacks[0]["attack"]["operation"] == 'pymysql.Cursor.execute'
    assert attacks[0]["attack"]["pathToPayload"] == '.dog_name'
    assert attacks[0]["attack"]["payload"] == '"Dangerous bobby\\", 1); -- "'
    assert attacks[0]["attack"]["source"] == "body"
    assert attacks[0]["attack"]["user"]["id"] == "123"
    assert attacks[0]["attack"]["user"]["name"] == "John Doe"


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
    assert attacks[0]["attack"]["blocked"] == True
    assert attacks[0]["attack"]["kind"] == "shell_injection"
    assert attacks[0]["attack"]['metadata']['command'] == 'ls -la'
    assert attacks[0]["attack"]["operation"] == 'subprocess.Popen'
    assert attacks[0]["attack"]["pathToPayload"] == '.command'
    assert attacks[0]["attack"]["payload"] == '"ls -la"'
    assert attacks[0]["attack"]["source"] == "route_params"
    assert attacks[0]["attack"]["user"]["id"] == "123"
    assert attacks[0]["attack"]["user"]["name"] == "John Doe"

def test_dangerous_response_with_firewall_query_params():
    res = requests.get(base_url_fw + "/create/via_query?dog_name=Malicious%20dog%22%2C%201)%3B%20--%20%ff")
    assert res.status_code == 500
    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    assert attacks[2]["attack"]["blocked"] == True
    assert attacks[2]["attack"]["kind"] == "sql_injection"
    assert attacks[0]["attack"]["operation"] == 'pymysql.Cursor.execute'
    assert attacks[2]["attack"]["pathToPayload"] == '.dog_name.[0]'
    assert attacks[2]["attack"]["payload"] == '"Malicious dog\\", 1); -- %FF"'
    assert attacks[2]["attack"]["source"] == "query"


def test_direct_imds_ips_are_still_ssrf_ips():
    imds_url = "http://169.254.169.254/metadata/test"
    res = requests.post(base_url_fw + "/request", data={'url': imds_url})
    assert res.status_code == 500

    time.sleep(5)  # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 4
    print(attacks[3]["attack"])
    assert attacks[3]["attack"]["blocked"] == True
    assert attacks[3]["attack"]["kind"] == "ssrf"
    assert attacks[3]["attack"]['metadata']['hostname'] == '169.254.169.254'
    assert attacks[3]["attack"]['metadata']['port'] == '80'
    assert attacks[3]["attack"]["operation"] == 'socket.getaddrinfo'
    assert attacks[3]["attack"]["path"] == '.url'
    assert attacks[3]["attack"]["payload"] == '"http://169.254.169.254/metadata/test"'
    assert attacks[3]["attack"]["source"] == "body"
    assert attacks[3]["attack"]["user"]["id"] == "123"
    assert attacks[3]["attack"]["user"]["name"] == "John Doe"

def test_dangerous_response_without_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(base_url_nofw + "/create", data={'dog_name': dog_name})
    assert res.status_code == 200

def test_ratelimiting_1_route():
    # First request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 200
    # Second request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 200
    # Third request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 429
    # Fourth request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 429

    time.sleep(5) # Wait until window expires
    
    # Fifth request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 200


def test_set_ip_forwarded_for():
    # IP allowed :
    res = requests.get(base_url_fw + "/", headers={
        "X-Forwarded-For": "1.1.1.1"
    })
    assert res.status_code == 200
    # IP Geo-blocked :
    res = requests.get(base_url_fw + "/", headers={
        "X-Forwarded-For": "1.2.3.4"
    })
    assert res.status_code == 403
    assert res.text == "Your IP address is blocked due to geo restrictions (Your IP: 1.2.3.4)"
