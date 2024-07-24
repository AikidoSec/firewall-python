""" This file simply exports the agent class"""

from datetime import datetime
import socket
import platform
import json
from copy import deepcopy
from aikido_firewall.helpers.logging import logger


class Agent:
    """Agent class"""

    timeout_in_sec = 5

    def __init__(self, block, api, token, serverless):
        self.block = block
        self.api = api
        self.token = token

        if isinstance(serverless, str) and len(serverless) == 0:
            raise ValueError("Serverless cannot be an empty string")
        self.serverless = serverless

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

            self.api.report(
                self.token,
                {
                    "type": "detected_attack",
                    "time": datetime.now(),
                    "agent": self.get_agent_info(),
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
        logger.debug("Aikido Agent : Sending out heartbeat")
        res = self.api.report(
            self.token,
            {
                "type": "heartbeat",
                "time": datetime.now(),
                "agent": self.get_agent_info(),
                "stats": {"sinks": [], "startedAt": 0, "endedAt": 0, "requests": []},
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
            {"type": "started", "time": datetime.now(), "agent": self.get_agent_info()},
            self.timeout_in_sec,
        )
        self.update_service_config(res)

    def get_agent_info(self):
        """
        This returns info about the agent
        """
        return {
            "dryMode": not self.block,
            "hostname": socket.gethostname(),
            "version": "x.x.x",
            "library": "firewall_python",
            "ipAddress": socket.gethostbyname(socket.gethostname()),
            "packages": [],
            "serverless": bool(self.serverless),
            "stack": [],
            "os": {"name": platform.system(), "version": platform.release()},
        }

    def update_service_config(self, res):
        """
        Update configuration based on the server's response
        """
