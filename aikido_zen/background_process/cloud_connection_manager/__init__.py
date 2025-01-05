""" This file simply exports the CloudConnectionManager class"""

import time
from aikido_zen.helpers.token import Token
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_zen.background_process.heartbeats import send_heartbeats_every_x_secs
from aikido_zen.background_process.routes import Routes
from aikido_zen.ratelimiting.rate_limiter import RateLimiter
from aikido_zen.helpers.logging import logger
from .update_blocked_ip_addresses import update_blocked_ip_addresses
from ..api.http_api import ReportingApiHTTP
from ..service_config import ServiceConfig
from ..users import Users
from ..hostnames import Hostnames
from ..realtime.start_polling_for_changes import start_polling_for_changes
from ..statistics import Statistics

# Import functions :
from .on_detected_attack import on_detected_attack
from .get_manager_info import get_manager_info
from .update_service_config import update_service_config
from .on_start import on_start
from .send_heartbeat import send_heartbeat


class CloudConnectionManager:
    """CloudConnectionManager class"""

    timeout_in_sec = 5  # Timeout of API calls to Aikido Server
    heartbeat_secs = 600  # Heartbeat every 10 minutes
    initial_stats_timeout = 60  # Wait 60 seconds after startup for initial stats

    def __init__(self, block, api, token, serverless):
        self.block = block
        self.api: ReportingApiHTTP = api
        self.token = token  # Should be instance of the Token class!
        self.routes = Routes(200)
        self.hostnames = Hostnames(200)
        self.conf = ServiceConfig(
            endpoints=[],
            last_updated_at=-1,  # Has not been updated yet
            blocked_uids=[],
            bypassed_ips=[],
            received_any_stats=True,
            blocked_ips=[],
        )
        self.rate_limiter = RateLimiter(
            max_items=5000, time_to_live_in_ms=120 * 60 * 1000  # 120 minutes
        )
        self.users = Users(1000)
        self.packages = {}
        self.statistics = Statistics(
            max_perf_samples_in_mem=5000, max_compressed_stats_in_mem=100
        )
        self.middleware_installed = False

        if isinstance(serverless, str) and len(serverless) == 0:
            raise ValueError("Serverless cannot be an empty string")
        self.serverless = serverless

    def start(self, event_scheduler):
        """Send out start event and add heartbeats"""
        res = self.on_start()
        if res.get("error", None) == "invalid_token":
            logger.info(
                "Token was invalid, not starting heartbeats and realtime polling."
            )
            return
        event_scheduler.enter(self.initial_stats_timeout, 1, self.report_initial_stats)
        send_heartbeats_every_x_secs(self, self.heartbeat_secs, event_scheduler)
        start_polling_for_changes(self, event_scheduler)

    def report_initial_stats(self):
        """
        This is run 1m after startup, and checks if we should send out
        a preliminary heartbeat with some stats.
        """
        data_is_available = not (
            self.statistics.is_empty() and len(self.routes.routes) <= 0
        )
        should_report_initial_stats = (
            data_is_available and not self.conf.received_any_stats
        )
        if should_report_initial_stats:
            self.send_heartbeat()

    def on_detected_attack(self, attack, context, blocked, stack):
        """This will send something to the API when an attack is detected"""
        return on_detected_attack(self, attack, context, blocked, stack)

    def on_start(self):
        """This will send out an Event signalling the start to the server"""
        return on_start(self)

    def send_heartbeat(self):
        """This will send a heartbeat to the server"""
        return send_heartbeat(self)

    def get_manager_info(self):
        """This returns info about the connection_manager"""
        return get_manager_info(self)

    def update_service_config(self, res):
        """Update configuration based on the server's response"""
        return update_service_config(self, res)

    def update_blocked_ip_addresses(self):
        """Will update service config with blocklist of IP addresses"""
        return update_blocked_ip_addresses(self)
