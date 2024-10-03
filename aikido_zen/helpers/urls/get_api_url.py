"""Helper file, see function docstring"""

import os
from urllib.parse import urlunparse
from aikido_zen.helpers.try_parse_url import try_parse_url

DEFAULT_API_URL = "https://guard.aikido.dev/"


def get_api_url():
    """Checks environment var AIKIDO_ENDPOINT for the api URL"""
    realtime_url = os.getenv("AIKIDO_ENDPOINT")
    if realtime_url is not None:
        parsed_url = try_parse_url(realtime_url)
        if parsed_url is None:
            return DEFAULT_API_URL  # Invalid URL
        if not parsed_url.path.endswith("/"):
            # Make sure ends with a slash :
            return urlunparse(parsed_url) + "/"
        return urlunparse(parsed_url)
    return DEFAULT_API_URL
