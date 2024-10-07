"""Exports class ThreadConfig"""
from threading import local
import aikido_zen.background_process.comms as comms
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_zen.background_process.routes.route_to_key import route_to_key
from .routes import Routes

THREAD_CONFIG_TLL_MS = 60 * 1000  # Time-To-Live is 60 seconds for the thread cache

threadlocal_storage = local()

def get_cache():
    """Returns the current ThreadCache"""
    return getattr(threadlocal_storage, "cache")


class ThreadCache:
    def __init__(self):
        # Load initial data :
        self.reset()
        self.renew()

        # Save as a thread-local object :
        threadlocal_storage.cache = self

    def route_init(self, route_metadata):
        """Registers a new route"""
        key = route_to_key(route_metadata)


    def get(self, route_metadata):
        """Returns the route's config data without modifying it"""
        key = route_to_key(route_metadata)
        if not key in self.routes:
            return None

    def is_bypassed_ip(self, ip):
        """Checks the given IP against the list of bypassed ips"""
        return ip in self.bypassed_ips

    def renew_if_ttl_expired(self):
        """Renews the data only if TTL has expired"""
        ttl_has_expired = (
            get_unixtime_ms(monotonic=True) - self.last_renewal > THREAD_CONFIG_TLL_MS
        )
        if ttl_has_expired:
            self.renew()

    def reset(self):
        """Empties out all values of the cache"""
        self.routes = Routes(max_size=1000)
        self.bypassed_ips = set()
        self.endpoints = []

    def renew(self):
        """
        Makes an IPC call to store the amount of hits and requests and renew the config
        """
        self.reset()
        res = comms.get_comms().send_data_to_bg_process(
            action="RENEW_CONFIG",
            obj={"current_routes": self.routes},
            receive=True,
        )
        if res["success"]:
            if isinstance(res["data"]["bypassed_ips"], set):
                self.bypassed_ips = res["data"]["bypassed_ips"]
            if isinstance(res["data"]["endpoints"], list):
                self.endpoints = res["data"]["endpoints"]
            if isinstance(res["data"]["routes"], dict):
                # Fix : 
                self.routes.load(res["data"]["routes"])
            self.last_renewal = get_unixtime_ms(monotonic=True)
        else:
            self.last_renewal = 0
