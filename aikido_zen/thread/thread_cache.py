"""Exports class ThreadConfig"""

import aikido_zen.background_process.comms as comms
from aikido_zen.background_process.routes import Routes
from aikido_zen.background_process.service_config import ServiceConfig
from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger
from aikido_zen.thread import process_worker_loader


class ThreadCache:
    """
    A process-local cache object that holds routes, bypassed ips, endpoints amount of requests
    """

    def __init__(self):
        self.reset()  # Initialize values

    def is_bypassed_ip(self, ip):
        """Checks the given IP against the list of bypassed ips"""
        return self.config.is_bypassed_ip(ip)

    def is_user_blocked(self, user_id):
        """Checks if the user id is blocked"""
        return user_id in self.config.blocked_uids

    def get_endpoints(self):
        return self.config.endpoints

    def reset(self):
        """Empties out all values of the cache"""
        self.routes = Routes(max_size=1000)
        self.config = ServiceConfig(
            endpoints=[],
            blocked_uids=set(),
            bypassed_ips=[],
            last_updated_at=-1,
            received_any_stats=False,
        )
        self.reqs = 0
        self.middleware_installed = False

    def renew(self):
        if not comms.get_comms():
            return

        # send stored data and receive new config and routes
        res = comms.get_comms().send_data_to_bg_process(
            action="SYNC_DATA",
            obj={
                "current_routes": dict(self.routes.routes),
                "reqs": self.reqs,
                "middleware_installed": self.middleware_installed,
            },
            receive=True,
        )
        if not res["success"] or not res["data"]:
            return

        self.reset()
        # update config
        if isinstance(res["data"].get("config"), ServiceConfig):
            self.config = res["data"]["config"]

        # update routes
        if isinstance(res["data"].get("routes"), dict):
            self.routes.routes = res["data"]["routes"]
            for route in self.routes.routes.values():
                route["hits_delta_since_sync"] = 0

    def increment_stats(self):
        """Increments the requests"""
        self.reqs += 1


# For these 2 functions and the data they process, we rely on Python's GIL
# See here: https://wiki.python.org/moin/GlobalInterpreterLock
global_thread_cache = ThreadCache()


def get_cache():
    """
    Returns the cache, protected by Python's GIL (so not our own mutex),
    and starts the process worker (which syncs info between the cache and agent), if it doesn't already exist.
    """
    global global_thread_cache
    process_worker_loader.load_worker()
    return global_thread_cache


def renew():
    global global_thread_cache
    global_thread_cache.renew()
