"""
Helper function file, see function docstring
"""

from urllib.parse import urlparse


def get_port_from_url(url):
    """
    Tries to retrieve a port number from the given url
    """
    parsed_url = urlparse(url)

    # Check if the port is specified and is a valid integer
    if parsed_url.port is not None:
        return parsed_url.port

    # Determine the default port based on the protocol
    if parsed_url.scheme == "https":
        return 443
    elif parsed_url.scheme == "http":
        return 80
