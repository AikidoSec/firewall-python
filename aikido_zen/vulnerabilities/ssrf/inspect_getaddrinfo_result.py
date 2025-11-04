"""
Mainly exports inspect_getaddrinfo_result function
"""

from aikido_zen.helpers.try_parse_url import try_parse_url
from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger
from aikido_zen.thread.thread_cache import get_cache
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

    ip_addresses = extract_ip_array_from_results(dns_results)
    imds_ip = resolves_to_imds_ip(ip_addresses, hostname)
    if imds_ip:
        return {
            "module": "socket",
            "operation": "socket.getaddrinfo",
            "kind": "stored_ssrf",
            "source": "",
            "path": "",
            "metadata": {"hostname": hostname, "privateIP": imds_ip},
            "payload": hostname,
        }

    if not ip_addresses_contain_private_ip(ip_addresses):
        return

    context = get_current_context()
    if not context:
        return  # Context should be set to check user input.
    if get_cache() and get_cache().is_bypassed_ip(context.remote_address):
        # We check for bypassed ip's here since it is not checked for us
        # in run_vulnerability_scan due to the exception for SSRF (see above code)
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
            "metadata": get_metadata_for_ssrf_attack(hostname, port),
            "payload": attack_findings["payload"],
        }


def get_metadata_for_ssrf_attack(hostname, port):
    """Returns metadata either with a port if it exists or just hostname"""
    if port:
        return {"hostname": hostname, "port": str(port)}
    return {"hostname": hostname}


def ip_addresses_contain_private_ip(ip_addresses) -> bool:
    return any(is_private_ip(ip) for ip in ip_addresses)
