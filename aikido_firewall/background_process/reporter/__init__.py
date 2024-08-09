""" This file simply exports the Reporter class"""

import time
from aikido_firewall.helpers.token import Token
from aikido_firewall.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_firewall.background_process.heartbeats import send_heartbeats_every_x_secs
from aikido_firewall.background_process.routes import Routes
from aikido_firewall.ratelimiting.rate_limiter import RateLimiter
from ..service_config import ServiceConfig
from ..users import Users
from ..hostnames import Hostnames

# Import functions :
from .on_detected_attack import on_detected_attack
from .get_reporter_info import get_reporter_info
from .update_service_config import update_service_config
from .on_start import on_start
from .send_heartbeat import send_heartbeat


class Reporter:
    """Reporter class"""

    timeout_in_sec = 5  # Timeout of API calls to Aikido Server
    heartbeat_secs = 600  # Heartbeat every 10 minutes

    def __init__(self, block, api, token, serverless):
        self.block = block
        self.api = api
        self.token = token  # Should be instance of the Token class!
        self.routes = Routes(200)
        self.hostnames = Hostnames(200)
        self.conf = ServiceConfig([], get_unixtime_ms(), [], [])
        self.rate_limiter = RateLimiter(
            max_items=5000, time_to_live_in_ms=120 * 60 * 1000  # 120 minutes
        )
        self.users = Users(1000)
        self.packages = {}

        if isinstance(serverless, str) and len(serverless) == 0:
            raise ValueError("Serverless cannot be an empty string")
        self.serverless = serverless

    def start(self, event_scheduler):
        """Send out start event and add heartbeats"""
        self.on_start()
        send_heartbeats_every_x_secs(self, self.heartbeat_secs, event_scheduler)

    def on_detected_attack(self, attack, context):
        """This will send something to the API when an attack is detected"""
        return on_detected_attack(self, attack, context)

    def on_start(self):
        """This will send out an Event signalling the start to the server"""
        return on_start(self)

    def send_heartbeat(self):
        """This will send a heartbeat to the server"""
        return send_heartbeat(self)

    def get_reporter_info(self):
        """This returns info about the reporter"""
        return get_reporter_info(self)

    def update_service_config(self, res):
        """Update configuration based on the server's response"""
        return update_service_config(self, res)
