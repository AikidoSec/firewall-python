""" This file simply exports the agent class"""

from datetime import datetime
from aikido_firewall.helpers.logging import logger


class Agent:
    """Agent class"""

    def __init__(self, block, api, token, serverless):
        self.block = block
        self.api = api
        self.token = token

        if isinstance(serverless, str) and len(serverless) == 0:
            raise ValueError("Serverless cannot be an empty string")
        self.serverless = serverless

    def on_detected_attack(self):
        """
        This will send something to the API when an attack is detected
        """
        if not self.token:
            return

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
        )
        self.update_service_config(res)

    def on_start(self):
        """
        This will send out an Event signalling the start to the server
        """
        if not self.token:
            return

    def get_agent_info(self):
        """
        This returns info about the agent
        """
        return {}

    def update_service_config(self, res):
        pass
