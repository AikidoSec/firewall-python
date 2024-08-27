"""Exports scan_for_ssrf_in_request function"""

from aikido_firewall.helpers.logging import logger
from .check_context_for_ssrf import check_context_for_ssrf
from .is_redirect_to_private_ip import is_redirect_to_private_ip


def scan_for_ssrf_in_request(url, port, operation, context):
    """Scans for SSRF attacks"""

    # Check if the request is a SSRF :
    context_contains_ssrf_results = check_context_for_ssrf(
        url.hostname, port, operation, context
    )
    if context_contains_ssrf_results:
        return context_contains_ssrf_results

    # Check if the request is a SSRF with redirects :
    logger.debug("Redirects : %s", context.outgoing_req_redirects)
    redirected_ssrf_results = is_redirect_to_private_ip(url, context)
    if redirected_ssrf_results:
        return {
            "operation": operation,
            "kind": "ssrf",
            "source": redirected_ssrf_results["source"],
            "pathToPayload": redirected_ssrf_results["pathToPayload"],
            "metadata": {},
            "payload": redirected_ssrf_results["payload"],
        }
