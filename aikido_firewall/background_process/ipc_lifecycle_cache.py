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

    def __init__(self, compressed_context):
        self.bypassed_ips = []
        self.matched_endpoints = []
        self.populate(compressed_context)
        self.save()

    def populate(self, compressed_context):
        """Fetches data over IPC"""
        # Fetch bypassed ips:
        res = get_comms().send_data_to_bg_process(
            action="GET_BYPASSED_IPS", obj=(), receive=True
        )
        if res["success"] and isinstance(res["data"], set):
            self.bypassed_ips = res["data"]

        # Fetch matched endpoints:
        res = get_comms().send_data_to_bg_process(
            action="MATCH_ENDPOINTS", obj=compressed_context, receive=True
        )
        if res["success"] and isinstance(res["data"], list):
            self.matched_endpoints = res["data"]

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
