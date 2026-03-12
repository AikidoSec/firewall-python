"""Helper function file"""

from urllib.parse import urlparse
from urllib3.util import parse_url

def try_parse_url(url):
    """Tries to parse the url using urlparse"""
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme and parsed_url.netloc:
            return parsed_url
        return None
    except Exception:
        return None

def try_lenient_parse_url(url):
    """Tries to parse the url using parse_url, which is more lenient than urlparse"""
    try:
        parsed_url = parse_url(url)
        if parsed_url.scheme and parsed_url.host:
            return parsed_url
        return None
    except Exception:
        return None
