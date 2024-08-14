"""
Mainly exports inspect_getaddrinfo_result function
"""

import traceback
from aikido_firewall.helpers.try_parse_url import try_parse_url
from aikido_firewall.context import get_current_context
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process import get_comms
from aikido_firewall.errors import AikidoSSRF
from aikido_firewall.helpers.blocking_enabled import is_blocking_enabled
from .imds import is_trusted_hostname, is_imds_ip_address
from .is_private_ip import is_private_ip
from .find_hostname_in_context import find_hostname_in_context


#  gets called when the result of the DNS resolution has come in
def inspect_getaddrinfo_result(dns_results, hostname, port):
    """Inspect the results of a getaddrinfo() call"""
    if not hostname or try_parse_url(hostname) is not None:
        #  If the hostname is an IP address, we don't need to inspect it
        logger.debug("Hostname %s is actually an IP address, ignoring", hostname)
        return

    context = get_current_context()

    ip_addresses = extract_ip_array_from_results(dns_results)
    if resolves_to_imds_ip(ip_addresses, hostname):
        #  Block stored SSRF attack that target IMDS IP addresses
        #  An attacker could have stored a hostname in a database that points to an IMDS IP address
        #  We don't check if the user input contains the hostname because there's no context
        if is_blocking_enabled():
            raise AikidoSSRF()

    if not context:
        return

    private_ip = next((ip for ip in ip_addresses if is_private_ip(ip)), None)
    if not private_ip:
        return

    found = find_hostname_in_context(hostname, context, port)
    if not found:
        return

    should_block = is_blocking_enabled()
    stack = " ".join(traceback.format_stack())
    attack = {
        "module": "socket",
        "operation": "socket.getaddrinfo",
        "kind": "ssrf",
        "source": found["source"],
        "blocked": should_block,
        "stack": stack,
        "path": found["pathToPayload"],
        "metadata": {"hostname": hostname},
        "payload": found["payload"],
    }
    logger.debug("Attack results : %s", attack)

    logger.debug("Sending data to bg process :")
    get_comms().send_data_to_bg_process("ATTACK", (attack, context, should_block))

    if should_block:
        raise AikidoSSRF()


def resolves_to_imds_ip(resolved_ip_addresses, hostname):
    """
    returns a boolean, true if the IP is an imds ip
    """
    #  Allow access to Google Cloud metadata service as you need to set specific headers to access it
    #  We don't want to block legitimate requests
    if is_trusted_hostname(hostname):
        return False
    return any(is_imds_ip_address(ip) for ip in resolved_ip_addresses)


def extract_ip_array_from_results(dns_results):
    """Extracts IP's from dns results"""
    ip_addresses = []
    for result in dns_results:
        ip_object = result[4]
        if ip_object is not None and ip_object[0] is not None:
            ip_addresses.append(ip_object[0])
    return ip_addresses
