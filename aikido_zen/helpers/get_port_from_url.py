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

    try:
        # Check if the port is specified and is a valid integer
        if parsed_url.port is not None:
            return parsed_url.port
    except ValueError:
        # This can happen if someone provides an invalid port, or if port is out of range
        # https://github.com/python/cpython/blob/fb1b51a58df4315f7ef3171a5abeb74f132b0971/Lib/urllib/parse.py#L184
        # Return None, in order to ensure we still match the hostname.
        return None

    # Determine the default port based on the protocol
    if parsed_url.scheme == "https":
        return 443
    if parsed_url.scheme == "http":
        return 80
