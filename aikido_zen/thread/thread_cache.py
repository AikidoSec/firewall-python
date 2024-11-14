"""Exports class ThreadConfig"""

from threading import local
import aikido_zen.background_process.comms as comms
import aikido_zen.helpers.get_current_unixtime_ms as t
from aikido_zen.background_process.routes import Routes
from aikido_zen.storage.service_config import ServiceConfig

THREAD_CONFIG_TTL_MS = 60 * 1000  # Time-To-Live is 60 seconds for the thread cache

threadlocal_storage = local()


def get_cache():
    """Returns the current ThreadCache"""
    cache = getattr(threadlocal_storage, "cache", None)
    if cache and isinstance(cache, ThreadCache):
        cache.renew_if_ttl_expired()
    if not cache:
        return ThreadCache()
    return cache


class ThreadCache:
    """
    A thread-local cache object that holds routes, bypassed ips, endpoints amount of requests
    With a Time-To-Live given by THREAD_CONFIG_TTL_MS
    """

    def __init__(self):
        # Load initial data :
        self.config = None
        self.last_renewal = -1
        self.routes = Routes(max_size=1000)
        self.reqs = 0
        self.renew()

        # Save as a thread-local object :
        threadlocal_storage.cache = self

    def is_bypassed_ip(self, ip):
        """Checks the given IP against the list of bypassed ips"""
        return self.config and self.config.is_bypassed_ip(ip)

    def is_user_blocked(self, user_id):
        """Checks if the user id is blocked"""
        return self.config and self.config.is_blocked_user(user_id)

    def renew_if_ttl_expired(self):
        """Renews the data only if TTL has expired"""
        ttl_has_expired = (
            t.get_unixtime_ms(monotonic=True) - self.last_renewal > THREAD_CONFIG_TTL_MS
        )
        if ttl_has_expired:
            self.renew()

    def renew(self):
        """
        Makes an IPC call to store the amount of hits and requests and renew the config
        """
        if not comms.get_comms():
            return
        res = comms.get_comms().send_data_to_bg_process(
            action="SYNC_DATA",
            obj={"current_routes": dict(self.routes.routes), "reqs": self.reqs},
            receive=True,
        )
        if res["success"]:
            self.reqs = 0
            if isinstance(res["data"]["service_config"], ServiceConfig):
                self.config = res["data"]["service_config"]
            if isinstance(res["data"]["routes"], dict):
                self.routes = Routes(max_size=1000)
                self.routes.routes = res["data"]["routes"]
                for route in self.routes.routes.values():
                    route["hits_delta_since_sync"] = 0
            self.last_renewal = t.get_unixtime_ms(monotonic=True)

    def increment_stats(self):
        """Increments the requests"""
        self.reqs += 1
