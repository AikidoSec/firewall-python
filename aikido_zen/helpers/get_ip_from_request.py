"""
Mainly exports the `get_ip_from_request` function
"""

import socket
import os
from typing import Optional

from aikido_zen.helpers.headers import Headers
from aikido_zen.helpers.ip_matcher import preparse
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.net.is_private_ip import is_private_ip
from aikido_zen.helpers.trust_proxy import (
    CIDRTrustProxy,
    CountTrustProxy,
    get_trust_proxy_config,
    is_trusted_proxy_request,
)


def get_ip_from_request(remote_address: str, headers: Headers) -> Optional[str]:
    """
    Tries and get the IP address from the request, checking for x-forwarded-for
    """
    ip_header = headers.get_header(get_ip_header_name())
    if ip_header and is_trusted_proxy_request(remote_address):
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
    config = get_trust_proxy_config()
    forwarded_ips = value.split(",")
    start = (
        len(forwarded_ips) - config.value
        if isinstance(config, CountTrustProxy)
        else len(forwarded_ips) - 1
    )
    for index in range(start, -1, -1):
        ip = normalize_ip(forwarded_ips[index].strip())
        if not is_ip(ip):
            continue
        normalized_ip = preparse(ip)
        if is_private_ip(normalized_ip):
            continue
        if isinstance(config, CIDRTrustProxy) and config.matcher.has(normalized_ip):
            continue
        return ip
    return None


def normalize_ip(ip: str) -> str:
    if is_ip(ip):
        return ip
    if ip.startswith("["):
        if ip.endswith("]"):
            return ip[1:-1]
        closing_bracket = ip.find("]:")
        if closing_bracket > 0:
            return ip[1:closing_bracket]
    parts = ip.split(":")
    if len(parts) == 2:
        return parts[0]
    return ip


def get_ip_header_name():
    # Allows for custom headers, which is useful depending on the proxy setup.
    if os.getenv("AIKIDO_CLIENT_IP_HEADER", None):
        client_ip_header = os.getenv("AIKIDO_CLIENT_IP_HEADER")
        return Headers.normalize_header_key(client_ip_header)

    # Default is the X-Forwarded-For header.
    return "X_FORWARDED_FOR"


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
