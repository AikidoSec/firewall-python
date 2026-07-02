"""
Helper module for token
"""

import os


class Token:
    """Class that encapsulates the token"""

    def __init__(self, token):
        if not isinstance(token, str):
            raise ValueError("Token should be an instance of string")
        if len(token) == 0:
            raise ValueError("Token cannot be an empty string")
        self.token = token

    def __str__(self):
        return self.token


def get_token_from_env():
    """
    Fetches the token from the env variable "AIKIDO_TOKEN"
    """
    aikido_token_env = os.getenv("AIKIDO_TOKEN")
    if aikido_token_env is not None:
        return Token(aikido_token_env)
    return None


def extract_region_from_token(token):
    """
    Extracts the region from a runtime token.

    New format: AIK_RUNTIME_{sys_group_id}_{service_id}_{region}_{random}
    Old format: AIK_RUNTIME_{sys_group_id}_{service_id}_{random}
    """
    if not token or not token.startswith("AIK_RUNTIME_"):
        return "EU"

    token_without_prefix = token[len("AIK_RUNTIME_") :]
    parts = token_without_prefix.split("_")

    if len(parts) == 4:
        return parts[2]

    return "EU"
