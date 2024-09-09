"""Exports get_redirect_origin function"""

import copy
from aikido_zen.helpers.get_port_from_url import get_port_from_url
from aikido_zen.helpers.urls.normalize_url import normalize_url


def compare_urls(dst, src):
    """Compares normalized urls"""
    if len(src) == 2:
        # Source is a hostname, port tuple. Check if it matches :
        port_matches = get_port_from_url(dst, parsed=True) == src[1]
        return dst.hostname == src[0] and port_matches

    normalized_dst = normalize_url(dst.geturl())
    normalized_src = normalize_url(src.geturl())
    return normalized_dst == normalized_src


def get_redirect_origin(redirects, hostname, port):
    """
    This function checks if the given URL is part of a redirect chain that is passed in the
    redirects parameter.
    It returns the origin of a redirect chain if the URL is the result of a redirect.
    The origin is the first URL in the chain, so the initial URL that was requested and redirected
    to the given URL or in case of multiple redirects the URL that was redirected to the given URL.

    Example:
    Redirect chain: A -> B -> C: getRedirectOrigin([A -> B, B -> C], C) => A
                               : getRedirectOrigin([A -> B, B -> C], B) => A
                               : getRedirectOrigin([A -> B, B -> C], D) => undefined
    """
    if not isinstance(redirects, list):
        return None
    current_url = copy.deepcopy((hostname, port))

    # Follow the redirect chain until we reach the origin or don't find a redirect

    while True:
        redirect = None
        for r in redirects:
            if compare_urls(r["destination"], current_url):
                redirect = r
        if not redirect:
            break
        current_url = redirect["source"]

    current_url_changed = current_url != (hostname, port)
    return current_url if current_url_changed else None
