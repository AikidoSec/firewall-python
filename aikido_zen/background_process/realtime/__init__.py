"""
Code to poll for realtime changes
"""

import os
import requests
from aikido_zen.helpers.logging import logger

api_url = "https://guard.aikido.dev/"


def get_realtime_url():
    """Fetches the default realtime url or environment variable"""
    realtime_url = os.getenv("AIKIDO_REALTIME_URL")
    if realtime_url is not None:
        return realtime_url
    return "https://runtime.aikido.dev/"


def get_config(token):
    """Fetches the config from realtime URL"""
    url = f"{api_url}api/runtime/config"
    headers = {
        "Authorization": str(token),
    }
    response = requests.get(url, headers=headers, timeout=3)  # timeout in 3 seconds
    if response.status_code != 200:
        logger.info("Invalid response from api : %s", response.status_code)

    return response.json()  # Parse and return the JSON response


def get_config_last_updated_at(token):
    """
    Fetches the time when the config was last updated from realtime server
    """
    url = f"{get_realtime_url()}config"
    headers = {
        "Authorization": str(token),
    }
    response = requests.get(url, headers=headers, timeout=0.5)  # timeout in 500ms
    if response.status_code != 200:
        logger.info("Invalid response from realtime api : %s", response.status_code)

    return int(response.json()["configUpdatedAt"])  #  Return configUpdatedAt time