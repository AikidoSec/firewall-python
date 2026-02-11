"""
Helper function file, see function docstring
"""
from urllib3.util import parse_url


def get_subdomains_from_url(url):
    """
    Returns a list with subdomains from url
    """
    if not isinstance(url, str):
        return []
    host = parse_url(url).hostname
    if not host:
        return []
    parts = host.split(".")
    return parts[:-2]
