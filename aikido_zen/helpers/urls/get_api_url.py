"""Helper file, see function docstring"""

import os
from urllib.parse import urlunparse
from aikido_zen.helpers.try_parse_url import try_parse_url
from aikido_zen.helpers.token import extract_region_from_token, get_token_from_env

DEFAULT_API_URL = "https://guard.aikido.dev/"
REGION_API_URLS = {
    "US": "https://guard.us.aikido.dev/",
    "ME": "https://guard.me.aikido.dev/",
    "AU": "https://guard.au.aikido.dev/",
}


def get_api_url():
    """Checks environment var AIKIDO_ENDPOINT for the api URL, falling back
    to a region-specific URL based on the AIKIDO_TOKEN"""
    realtime_url = os.getenv("AIKIDO_ENDPOINT")
    if realtime_url is not None:
        parsed_url = try_parse_url(realtime_url)
        if parsed_url is None:
            return DEFAULT_API_URL  # Invalid URL
        if not parsed_url.path.endswith("/"):
            # Make sure ends with a slash :
            return urlunparse(parsed_url) + "/"
        return urlunparse(parsed_url)

    token = get_token_from_env()
    region = extract_region_from_token(str(token) if token else "")
    return REGION_API_URLS.get(region, DEFAULT_API_URL)
