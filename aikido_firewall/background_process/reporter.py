""" This file simply exports the Reporter class"""

import time
import socket
import platform
import json
from copy import deepcopy
from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.limit_length_metadata import limit_length_metadata
from aikido_firewall.helpers.token import Token
from aikido_firewall.helpers.get_machine_ip import get_ip
from aikido_firewall.helpers.get_ua_from_context import get_ua_from_context
from aikido_firewall.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_firewall import PKG_VERSION
from aikido_firewall.background_process.heartbeats import send_heartbeats_every_x_secs
from aikido_firewall.background_process.routes import Routes
from .reporter_config import ReporterConfig


class Reporter:
    """Reporter class"""

    timeout_in_sec = 5  # Timeout of API calls to Aikido Server
    heartbeat_secs = 10  # Heartbeat every 10 minutes

    def __init__(self, block, api, token, serverless, event_scheduler):
        self.block = block
        self.api = api
        self.token = token  # Should be instance of the Token class!
        self.routes = Routes(200)
        self.conf = ReporterConfig([], get_unixtime_ms())

        if isinstance(serverless, str) and len(serverless) == 0:
            raise ValueError("Serverless cannot be an empty string")
        self.serverless = serverless

        self.on_start()
        send_heartbeats_every_x_secs(self, self.heartbeat_secs, event_scheduler)

    def on_detected_attack(self, attack, context):
        """
        This will send something to the API when an attack is detected
        """
        if not self.token:
            return
        # Modify attack so we can send it out :
        try:
            attack["user"] = None
            attack["payload"] = json.dumps(attack["payload"])[:4096]
            attack["metadata"] = limit_length_metadata(attack["metadata"], 4096)
            attack["blocked"] = self.block

            payload = {
                "type": "detected_attack",
                "time": get_unixtime_ms(),
                "agent": self.get_reporter_info(),
                "attack": attack,
                "request": {
                    "method": context.method,
                    "url": context.url,
                    "ipAddress": context.remote_address,
                    "userAgent": get_ua_from_context(context),
                    "body": context.body,
                    "headers": context.headers,
                    "source": context.source,
                    "route": context.route,
                },
            }
            logger.debug(json.dumps(payload))
            result = self.api.report(
                self.token,
                payload,
                self.timeout_in_sec,
            )
            logger.debug("Result : %s", result)
        except Exception as e:
            logger.debug(e)
            logger.info("Failed to report attack")

    def send_heartbeat(self):
        """
        This will send a heartbeat to the server
        """
        if not self.token:
            return
        logger.debug("Aikido Reporter : Sending out heartbeat")
        res = self.api.report(
            self.token,
            {
                "type": "heartbeat",
                "time": get_unixtime_ms(),
                "agent": self.get_reporter_info(),
                "stats": {
                    "sinks": {},
                    "startedAt": 0,
                    "endedAt": 0,
                    "requests": {
                        "total": 0,
                        "aborted": 0,
                        "attacksDetected": {
                            "total": 0,
                            "blocked": 0,
                        },
                    },
                },
                "hostnames": [],
                "routes": list(self.routes),
                "users": [],
            },
            self.timeout_in_sec,
        )
        self.update_service_config(res)

    def on_start(self):
        """
        This will send out an Event signalling the start to the server
        """
        if not self.token:
            return
        res = self.api.report(
            self.token,
            {
                "type": "started",
                "time": get_unixtime_ms(),
                "agent": self.get_reporter_info(),
            },
            self.timeout_in_sec,
        )
        self.update_service_config(res)

    def get_reporter_info(self):
        """
        This returns info about the reporter
        """
        return {
            "dryMode": not self.block,
            "hostname": socket.gethostname(),
            "version": PKG_VERSION,
            "library": "firewall_python",
            "ipAddress": get_ip(),
            "packages": [],
            "serverless": bool(self.serverless),
            "stack": [],
            "os": {"name": platform.system(), "version": platform.release()},
            "preventedPrototypePollution": False,  # Get this out of the API maybe?
            "nodeEnv": "",
        }

    def update_service_config(self, res):
        """
        Update configuration based on the server's response
        """
        if res["success"] is False:
            logger.debug(res)
            return
        if "block" in res.keys() and res["block"] != self.block:
            logger.debug("Updating blocking, setting blocking to : %s", res["block"])
            self.block = bool(res["block"])

        if res["endpoints"]:
            if not isinstance(res["endpoints"], list):
                res["endpoints"] = []  # Empty list
            self.conf = ReporterConfig(
                endpoints=res["endpoints"], last_updated_at=get_unixtime_ms()
            )
