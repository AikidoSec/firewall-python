""" This file simply exports the agent class"""


class Agent:
    """Agent class"""

    def __init__(self, block, api, token, serverless):
        self.block = block
        self.api = api
        self.token = token

        if isinstance(serverless, str) and len(serverless) == 0:
            raise ValueError("Serverless cannot be an empty string")
        self.serverless = serverless
