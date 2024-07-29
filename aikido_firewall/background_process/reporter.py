""" This file simply exports the Reporter class"""

import time
import socket
import platform
import json
from copy import deepcopy
from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.limit_length_metadata import limit_length_metadata
from aikido_firewall.helpers.token import Token
from aikido_firewall import PKG_VERSION


class Reporter:
    """Reporter class"""

    timeout_in_sec = 5

    def __init__(self, block, api, token, serverless):
        self.block = block
        self.api = api
        self.token = token  # Should be instance of the Token class!

        if isinstance(serverless, str) and len(serverless) == 0:
            raise ValueError("Serverless cannot be an empty string")
        self.serverless = serverless

        self.on_start()

    def on_detected_attack(self, attack):
        """
        This will send something to the API when an attack is detected
        """
        if not self.token:
            return
        # Modify attack so we can send it out :
        try:
            req = deepcopy(attack["request"])
            del attack["request"]
            attack["user"] = req["user"]
            attack["payload"] = json.dumps(attack["payload"])[:4096]
            attack["metadata"] = limit_length_metadata(attack["metadata"], 4096)

            self.api.report(
                self.token,
                {
                    "type": "detected_attack",
                    "time": get_unixtime_ms(),
                    "agent": self.get_reporter_info(),
                    "attack": attack,
                    "request": {
                        "method": req["method"],
                        "url": req["url"],
                        "ipAddress": req["remoteAddress"],
                        "userAgent": "WIP",
                        "body": {},
                        "headers": {},
                        "source": req["source"],
                        "route": req["route"],
                    },
                },
                self.timeout_in_sec,
            )
        except Exception:
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
                "routes": [],
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
        if res["block"] and res["block"] != self.block:
            logger.debug("Updating blocking, setting blocking to : %s", res["block"])
            self.block = bool(res["block"])
        print(res)


def get_unixtime_ms():
    """Get the current unix time but in ms"""
    return int(time.time() * 1000)


def get_ip():
    """Tries to fetch the IP and returns 0.0.0.0 on failure"""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "0.0.0.0"
