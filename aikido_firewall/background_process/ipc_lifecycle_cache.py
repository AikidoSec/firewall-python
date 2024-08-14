"""
Contains the `IPCLifecycleCache` cache
"""

import threading
from .comms import get_comms

local = threading.local()


def get_cache():
    """Returns the current cache"""
    try:
        return local.ipc_lifecycle_cache
    except AttributeError:
        return None


class IPCLifecycleCache:
    """Threading-local storage object"""

    def __init__(self, context):
        self.bypassed_ips = []
        self.matched_endpoints = []
        self.populate(context)
        self.save()

    def populate(self, context):
        """Fetches data over IPC"""
        # Fetch bypassed ips:
        res = get_comms().send_data_to_bg_process(
            action="FETCH_INITIAL_METADATA",
            obj={"context_metadata": context.get_metadata()},
            receive=True,
        )
        if res["success"]:
            if isinstance(res["data"]["bypassed_ips"], set):
                self.bypassed_ips = res["data"]["bypassed_ips"]
            if isinstance(res["data"]["matched_endpoints"], list):
                self.matched_endpoints = res["data"]["matched_endpoints"]

    def is_bypassed_ip(self, ip):
        """Checks if the ip is present in the bypassed_ips list"""
        return ip in self.bypassed_ips

    def protection_forced_off(self):
        """Checks the stored matches for forceProtectionOff"""
        if len(self.matched_endpoints) > 0:
            return self.matched_endpoints[0]["endpoint"]["forceProtectionOff"]
        return False

    def save(self):
        """Save the current cache"""
        local.ipc_lifecycle_cache = self
