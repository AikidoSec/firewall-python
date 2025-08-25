import time
import requests

from .event_handler import EventHandler
from .assert_equals import assert_eq
from .request import Request
from .test_payloads_safe_vs_unsafe import test_payloads_safe_vs_unsafe

class App:
    def __init__(self, port):
        self.urls = {
            "enabled": f"http://localhost:{port}",
            "disabled": f"http://localhost:{port + 1}"
        }
        self.payloads = {}
        self.event_handler = EventHandler()
        if not wait_until_live(self.urls["enabled"]):
            raise Exception(self.urls["enabled"] + " is not turning on.")
        if not wait_until_live(self.urls["disabled"]):
            raise Exception(self.urls["disabled"] + " is not turning on.")

    def add_payload(self,key, safe_request, unsafe_request=None, test_event=None):
        self.payloads[key] = {
            "safe": safe_request,
            "unsafe": unsafe_request,
            "test_event": test_event
        }

    def test_payload(self, key):
        if key not in self.payloads:
            raise Exception("Payload " + key + " not found.")
        payload = self.payloads.get(key)

        self.event_handler.reset()
        test_payloads_safe_vs_unsafe(payload, self.urls)
        print("✅ Tested payload: " + key)

        if not payload["test_event"]:
            return # Finished tests.

        time.sleep(5)
        attacks = self.event_handler.fetch_attacks()
        assert_eq(len(attacks), equals=1)
        if isinstance(payload["test_event"], dict):
            for k, v in payload["test_event"].items():
                if k == "user_id":  # exemption rule for user ids
                    assert_eq(attacks[0]["attack"]["user"]["id"], v)
                else:
                    assert_eq(attacks[0]["attack"][k], equals=v)
            print("✅ Tested accurate event reporting for: " + key)

    def test_all_payloads(self):
        for key in self.payloads.keys():
            self.test_payload(key)

    def get_heartbeat(self):
        print("↺ Fetching latest heartbeat")
        heartbeats = self.event_handler.fetch_heartbeats()
        while len(heartbeats) == 0:
            heartbeats = self.event_handler.fetch_heartbeats()
            time.sleep(5)
        assert_eq(len(heartbeats), equals=1)
        return heartbeats[0]

def wait_until_live(url):
    for i in range(10):
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                print("Server is live: " + url)
                return True
            else:
                print("Status code " + str(res.status_code) + " for " + url)
        except requests.RequestException as e:
            print(f"Request failed: {e}")
        time.sleep(5)
    return False
