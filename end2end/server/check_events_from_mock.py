import requests
import json

def fetch_events_from_mock(url):
    mock_events_url = f"{url}/mock/events"
    res = requests.get(mock_events_url, timeout=5)
    json_events = json.loads(res.content.decode("utf-8"))
    return json_events

def filter_on_event_type(events, type):
    return [event for event in events if event["type"] == type]

def validate_started_event(event, stack, dry_mode=False, serverless=False, os_name="Linux", platform="CPython"):
    assert event["agent"]["dryMode"] == dry_mode
    assert event["agent"]["library"] == "firewall-python"
    assert event["agent"]["nodeEnv"] == ""
    assert event["agent"]["os"]["name"] == os_name
    assert event["agent"]["platform"]["name"] == platform
    assert event["agent"]["serverless"] ==  serverless
    assert set(event["agent"]["stack"]) == set(stack)

events = fetch_events_from_mock("http://localhost:5000")
started_events = filter_on_event_type(events, "started")
validate_started_event(started_events[0], ["pymysql", "flask"])
print(started_events)
