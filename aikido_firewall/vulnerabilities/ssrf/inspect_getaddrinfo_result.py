"""
Mainly exports inspect_getaddrinfo_result function
"""

from aikido_firewall.helpers.try_parse_url import try_parse_url
from aikido_firewall.context import get_current_context
from aikido_firewall.helpers.logging import logger
from aikido_firewall.errors import AikidoSSRF
from aikido_firewall.helpers.blocking_enabled import is_blocking_enabled
from .imds import resolves_to_imds_ip
from .is_private_ip import is_private_ip
from .find_hostname_in_context import find_hostname_in_context
from .extract_ip_array_from_results import extract_ip_array_from_results
from .is_redirect_to_private_ip import is_redirect_to_private_ip


#  gets called when the result of the DNS resolution has come in
def inspect_getaddrinfo_result(dns_results, hostname, port):
    """Inspect the results of a getaddrinfo() call"""
    if not hostname or try_parse_url(hostname) is not None:
        #  If the hostname is an IP address, we don't need to inspect it
        logger.debug("Hostname %s is actually an IP address, ignoring", hostname)
        return

    context = get_current_context()
    if not inspect_dns_results(dns_results, hostname):
        return

    if not context:
        return

    # attack_findings is an object containing source, pathToPayload and payload.
    attack_findings = find_hostname_in_context(hostname, context, port)
    if not attack_findings:
        # Hostname/port not found in context, checking for redirects
        logger.debug("Redirects : %s", context.outgoing_req_redirects)
        attack_findings = is_redirect_to_private_ip(hostname, context, port)

    if attack_findings:
        return {
            "module": "socket",
            "operation": "socket.getaddrinfo",
            "kind": "ssrf",
            "source": attack_findings["source"],
            "path": attack_findings["pathToPayload"],
            "metadata": {"hostname": hostname},
            "payload": attack_findings["payload"],
        }


def inspect_dns_results(dns_results, hostname):
    """
    Blocks stored SSRF attack that target IMDS IP addresses and returns True
    if a private_ip is present.
    This function gets called by inspect_getaddrinfo_result after parsing the hostname.
    """
    ip_addresses = extract_ip_array_from_results(dns_results)
    if resolves_to_imds_ip(ip_addresses, hostname):
        #  An attacker could have stored a hostname in a database that points to an IMDS IP address
        #  We don't check if the user input contains the hostname because there's no context
        if is_blocking_enabled():
            raise AikidoSSRF()

    private_ip = next((ip for ip in ip_addresses if is_private_ip(ip)), None)
    return private_ip
