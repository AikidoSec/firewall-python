"""
Mainly exports the `get_ip_from_request` function
"""

import socket
import os
from aikido_zen.helpers.logging import logger


def get_ip_from_request(remote_address, headers):
    """
    Tries and get the IP address from the request, checking for x-forwarded-for
    """
    if headers:
        lower_headers = {key.lower(): value for key, value in headers.items()}
        if "x_forwarded_for" in lower_headers and trust_proxy():
            x_forwarded_for = get_client_ip_from_x_forwarded_for(
                lower_headers["x_forwarded_for"]
            )

            if x_forwarded_for and is_ip(x_forwarded_for):
                return x_forwarded_for

    if remote_address and is_ip(remote_address):
        return remote_address

    return None


def get_client_ip_from_x_forwarded_for(value):
    """
    Fetches the IP out of the X-Forwarder-For headers
    """
    forwarded_ips = [ip.strip() for ip in value.split(",")]

    for ip in forwarded_ips:
        if ":" in ip:
            parts = ip.split(":")
            if len(parts) == 2:
                return parts[0]

    for ip in forwarded_ips:
        if is_ip(ip):
            return ip

    return None


def trust_proxy():
    """
    Checks the enviornment variables for `AIKIDO_TRUST_PROXY`
    """
    return not "AIKIDO_TRUST_PROXY" in os.environ or os.environ[
        "AIKIDO_TRUST_PROXY"
    ] in ["1", "true"]


def is_ip(value):
    """
    Checks if `value` is a vlid IPv4 or IPv6 ip
    """
    try:
        socket.inet_pton(socket.AF_INET, value)  # Check for IPv4
        return True
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, value)  # Check for IPv6
            return True
        except socket.error:
            return False
    except Exception as e:
        logger.debug("is_ip failed because of exception : %s", e)
        return False
