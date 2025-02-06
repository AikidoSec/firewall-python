import requests
import json

def fetch_events_from_mock(url):
    mock_events_url = f"{url}/mock/events"
    res = requests.get(mock_events_url, timeout=5)
    json_events = json.loads(res.content.decode("utf-8"))
    return json_events

def filter_on_event_type(events, type):
    return [event for event in events if event["type"] == type]

def validate_heartbeat(event, routes, req_stats):
    assert event["type"] == "heartbeat"
    assert event["routes"] == routes
    assert event["stats"]["requests"] == req_stats
