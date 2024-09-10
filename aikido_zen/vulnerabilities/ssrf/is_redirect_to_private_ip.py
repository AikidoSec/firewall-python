"""Exports is_redirect_to_private_ip"""

from aikido_zen.helpers.get_port_from_url import get_port_from_url
from .get_redirect_origin import get_redirect_origin
from .find_hostname_in_context import find_hostname_in_context


def is_redirect_to_private_ip(hostname, context, port):
    """
    This function is called before an outgoing request is made.
    It's used to prevent requests to private IP addresses after a redirect with
        a user-supplied URL (SSRF).
    It returns True if the following conditions are met:
    - context.outgoing_req_redirects is set: Inside the context of this incoming request,
        there was a redirect
    - The hostname of the URL contains a private IP address
    - The redirect origin, so the user-supplied hostname and port that caused the first redirect,
        is found in the context of the incoming request
    """
    if context.outgoing_req_redirects:
        redirect_origin = get_redirect_origin(
            context.outgoing_req_redirects, hostname, port
        )
        if redirect_origin:
            origin_hostname = getattr(redirect_origin, "hostname")
            origin_port = get_port_from_url(redirect_origin, parsed=True)
            return find_hostname_in_context(origin_hostname, context, origin_port)

    return None
