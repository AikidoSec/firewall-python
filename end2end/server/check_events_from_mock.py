import requests
import json

def fetch_events_from_mock(url):
    mock_events_url = f"{url}/mock/events"
    res = requests.get(mock_events_url, timeout=5)
    json_events = json.loads(res.content.decode("utf-8"))
    return json_events

def clear_events_from_mock(url):
    mock_events_url = f"{url}/mock/reset"
    res = requests.get(mock_events_url, timeout=5)
    return json.loads(res.content.decode("utf-8"))


def filter_on_event_type(events, type):
    return [event for event in events if event["type"] == type]

def validate_started_event(event, stack, dry_mode=False, serverless=False, os_name="Linux", platform="CPython"):
    assert event["agent"]["dryMode"] == dry_mode
    assert event["agent"]["library"] == "firewall-python"
    assert event["agent"]["nodeEnv"] == ""
    assert event["agent"]["os"]["name"] == os_name
    assert event["agent"]["platform"]["name"] == platform
    assert event["agent"]["serverless"] ==  serverless
    # # Check for packages is disabled until we start using them in core : 
    # if stack is not None:
    #    assert set(event["agent"]["stack"]) == set(stack)

def validate_heartbeat(event, routes=None, req_stats=None, packages=None):
    assert event["type"] == "heartbeat", f"Expected event type 'heartbeat', but got '{event['type']}'"
    if packages:
        package_names = set(map(lambda x: x["name"], event["packages"]))
        assert package_names == packages, f"Expected {packages} but got {package_names}"
    if routes:
        assert event["routes"] == routes, f"Expected routes '{routes}', but got '{event['routes']}'"
    if req_stats:
        assert event["stats"]["requests"] == req_stats, f"Expected request stats '{req_stats}', but got '{event['stats']['requests']}'"

