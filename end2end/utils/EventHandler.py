import time
import requests
import json

class EventHandler:
    def __init__(self, url="http://localhost:5000"):
        self.url = url
    def reset(self):
        print("Resetting stored events on mock server")
        res = requests.get(self.url + "/mock/reset", timeout=5)
        time.sleep(1)
    def fetch_events_from_mock(self):
        res = requests.get(self.url + "/mock/events", timeout=5)
        json_events = json.loads(res.content.decode("utf-8"))
        return json_events
    def fetch_attacks(self):
        return filter_on_event_type(self.fetch_events_from_mock(), "detected_attack")

def filter_on_event_type(events, type):
    return [event for event in events if event["type"] == type]