"""
Mainly exports the `get_ip_from_request` function
"""

import socket
import os
from typing import Optional

from aikido_zen.helpers.headers import Headers
from aikido_zen.helpers.logging import logger


def get_ip_from_request(remote_address: str, headers: Headers) -> Optional[str]:
    """
    Tries and get the IP address from the request, checking for x-forwarded-for
    """
    header_name = Headers.normalize_header_key(get_ip_header_name())
    return resolve_client_ip(remote_address, headers.get_header(header_name))


def resolve_client_ip(remote_address: str, ip_header: Optional[str]) -> Optional[str]:
    if ip_header and trust_proxy():
        ip_header_value = get_client_ip_from_header(ip_header)

        if ip_header_value and is_ip(ip_header_value):
            return ip_header_value

    if remote_address and is_ip(remote_address):
        return remote_address

    return None


def get_client_ip_from_header(value):
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
    Checks the environment variables for `AIKIDO_TRUST_PROXY`, Defaults to true.
    """
    trust_proxy_env = os.getenv("AIKIDO_TRUST_PROXY")
    if not trust_proxy_env:
        return True  # default to trusting proxy

    if trust_proxy_env.lower() in ["0", "false"]:
        return False
    return True


def get_ip_header_name():
    return os.getenv("AIKIDO_CLIENT_IP_HEADER") or "X-Forwarded-For"


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
