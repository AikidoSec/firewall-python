"""Exports class ThreadConfig"""

import aikido_zen.background_process.comms as comms
from aikido_zen.background_process.packages import PackagesStore
from aikido_zen.background_process.routes import Routes
from aikido_zen.background_process.service_config import ServiceConfig
from aikido_zen.storage.ai_statistics import AIStatistics
from aikido_zen.storage.hostnames import Hostnames
from aikido_zen.storage.statistics import Statistics
from aikido_zen.storage.users import Users
from aikido_zen.thread import process_worker_loader


class ThreadCache:
    """
    A process-local cache object that holds routes, bypassed ips, endpoints amount of requests
    """

    def __init__(self):
        self.hostnames = Hostnames(200)
        self.users = Users(1000)
        self.stats = Statistics()
        self.ai_stats = AIStatistics()
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
        self.middleware_installed = False
        self.hostnames.clear()
        self.users.clear()
        self.stats.clear()
        self.ai_stats.clear()
        PackagesStore.clear()

    def renew(self):
        if not comms.get_comms():
            return

        # send stored data and receive new config and routes
        res = comms.get_comms().send_data_to_bg_process(
            action="SYNC_DATA",
            obj={
                "current_routes": self.routes.get_routes_with_hits(),
                "middleware_installed": self.middleware_installed,
                "hostnames": self.hostnames.as_array(),
                "users": self.users.as_array(),
                "stats": self.stats.get_record(),
                "ai_stats": self.ai_stats.get_stats(),
                "packages": PackagesStore.export(),
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
