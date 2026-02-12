"""
Helper function file, see function docstring
"""

from urllib.parse import urlparse


def get_subdomains_from_url(url):
    """
    Returns a list with subdomains from url
    """
    if not isinstance(url, str):
        return []
    host = urlparse(url).hostname
    if not host:
        return []
    parts = host.split(".")
    return parts[:-2]
