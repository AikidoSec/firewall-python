"""This file simply exports the CloudConnectionManager class"""

from aikido_zen.background_process.heartbeats import start_heartbeats
from aikido_zen.background_process.routes import Routes
from aikido_zen.ratelimiting.rate_limiter import RateLimiter
from aikido_zen.helpers.logging import logger
from .update_firewall_lists import update_firewall_lists
from ..api.http_api import ReportingApiHTTP
from ..service_config import ServiceConfig
from aikido_zen.storage.users import Users
from aikido_zen.storage.hostnames import Hostnames
from ..realtime.start_polling_for_changes import start_polling_for_changes
from ..realtime.listen_for_config_updates import listen_for_config_updates
from ...helpers.get_current_unixtime_ms import get_unixtime_ms
from ...storage.ai_statistics import AIStatistics
from ...storage.firewall_lists import FirewallLists
from ...storage.statistics import Statistics
from aikido_zen.helpers.env_vars.feature_flags import is_feature_enabled

# Import functions :
from .get_manager_info import get_manager_info
from .update_service_config import update_service_config
from .on_start import on_start
from .send_heartbeat import send_heartbeat


class CloudConnectionManager:
    """CloudConnectionManager class"""

    timeout_in_sec = 30  # Timeout of API calls to Aikido Server
    heartbeat_secs = 600  # Heartbeat every 10 minutes

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
        )
        self.firewall_lists = FirewallLists()
        self.rate_limiter = RateLimiter(
            max_items=5000, time_to_live_in_ms=120 * 60 * 1000  # 120 minutes
        )
        self.users = Users(1000)
        self.statistics = Statistics()
        self.ai_stats = AIStatistics()
        self.middleware_installed = False

        if isinstance(serverless, str) and len(serverless) == 0:
            raise ValueError("Serverless cannot be an empty string")
        self.serverless = serverless

    def start(self, event_scheduler):
        """Send out start event and add heartbeats"""
        res = on_start(self)
        if res.get("error", None) == "invalid_token":
            logger.info(
                "Token was invalid, not starting heartbeats and realtime polling."
            )
            return
        start_heartbeats(self, event_scheduler)
        start_polling_for_changes(self, event_scheduler)

        if is_feature_enabled("sse") or self.conf.is_feature_enabled(
            "realtime_updates"
        ):
            listen_for_config_updates(self, event_scheduler)

    def send_heartbeat(self):
        """This will send a heartbeat to the server"""
        return send_heartbeat(self)

    def update_service_config(self, res):
        """Update configuration based on the server's response"""
        return update_service_config(self, res)

    def update_firewall_lists(self):
        """Will update service config with blocklist of IP addresses"""
        return update_firewall_lists(self)

    def report_api_event(self, event):
        if not self.token:
            return {"success": False, "error": "invalid_token"}
        try:
            payload = {
                "time": get_unixtime_ms(),
                "agent": get_manager_info(self),
            }
            payload.update(event)  # Merge default fields with event fields

            result = self.api.report(self.token, payload, self.timeout_in_sec)
            if not result.get("success", True):
                logger.error(
                    "CloudConnectionManager: Reporting to api failed, error=%s",
                    result.get("error", "unknown"),
                )
            return result
        except Exception as e:
            logger.debug(e)
            logger.error(
                "CloudConnectionManager: Reporting to api failed, unexpected error (see debug logs)"
            )
