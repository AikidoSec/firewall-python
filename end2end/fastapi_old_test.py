import time
import requests
from .server.check_events_from_mock import (
    fetch_events_from_mock,
    filter_on_event_type,
    validate_started_event,
    validate_heartbeat,
)

base_url_fw = "http://localhost:8114"
base_url_nofw = "http://localhost:8115"


def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], None)


def test_homepage_with_firewall():
    res = requests.get(f"{base_url_fw}/")
    assert res.status_code == 200


def test_homepage_without_firewall():
    res = requests.get(f"{base_url_nofw}/")
    assert res.status_code == 200


def test_sync_route_with_firewall():
    res = requests.get(f"{base_url_fw}/sync_route")
    assert res.status_code == 200


def test_sync_route_without_firewall():
    res = requests.get(f"{base_url_nofw}/sync_route")
    assert res.status_code == 200


def test_shell_injection_with_firewall():
    res = requests.get(f"{base_url_fw}/shell/ls;echo test")
    assert res.status_code == 500

    time.sleep(5)
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 1
    assert attacks[0]["attack"]["blocked"] == True
    assert attacks[0]["attack"]["kind"] == "shell_injection"
    assert attacks[0]["attack"]["operation"] == "subprocess.Popen"
    assert attacks[0]["attack"]["source"] == "routeParams"


def test_shell_injection_without_firewall():
    res = requests.get(f"{base_url_nofw}/shell/ls")
    assert res.status_code == 200


def test_initial_heartbeat():
    time.sleep(55)
    events = fetch_events_from_mock("http://localhost:5000")
    heartbeat_events = filter_on_event_type(events, "heartbeat")
    assert len(heartbeat_events) == 1
    routes = heartbeat_events[0]["routes"]
    route_paths = sorted([r["path"] for r in routes])
    assert "/" in route_paths
    assert "/sync_route" in route_paths
