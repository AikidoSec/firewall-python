"""
Code to poll for realtime changes
"""

import os

from aikido_zen.background_process.api.helpers import InternalRequest
from aikido_zen.helpers.urls.get_api_url import get_api_url


def get_realtime_url():
    """Fetches the default realtime url or environment variable"""
    realtime_url = os.getenv("AIKIDO_REALTIME_ENDPOINT")
    if realtime_url is not None:
        if not realtime_url.endswith("/"):
            realtime_url += "/"
        return realtime_url
    return "https://runtime.aikido.dev/"


def get_config(token):
    """Fetches the config from realtime URL"""
    url = get_api_url() + "api/runtime/config"
    headers = {
        "Authorization": str(token),
    }
    return InternalRequest.get(url, headers=headers, timeout=3)


def get_config_last_updated_at(token) -> int:
    """
    Fetches the time when the config was last updated from realtime server
    """
    url = f"{get_realtime_url()}config"
    headers = {
        "Authorization": str(token),
    }
    response = InternalRequest.get(url, headers=headers, timeout=0.5)
    config_updated_at = response.json.get("configUpdatedAt", 0)
    return int(config_updated_at)
