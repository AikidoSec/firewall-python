"""
Helper function file, see function docstring
"""

from urllib.parse import urlparse


def get_port_from_url(url, parsed=False):
    """
    Tries to retrieve a port number from the given url
    """
    if not parsed:
        parsed_url = urlparse(url)
    else:
        parsed_url = url

    # Check if the port is specified and is a valid integer
    if parsed_url.port is not None:
        return parsed_url.port

    # Determine the default port based on the protocol
    if parsed_url.scheme == "https":
        return 443
    if parsed_url.scheme == "http":
        return 80
