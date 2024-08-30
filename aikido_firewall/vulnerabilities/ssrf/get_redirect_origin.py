"""Exports get_redirect_origin function"""

import copy
from urllib.parse import urlparse, urlunparse
from aikido_firewall.helpers.urls.normalize_url import normalize_url


    """Normalizes the url"""

def compare_urls(url1, url2):
    """Compares normalized urls"""
    normalized_url1 = normalize_url(url1.geturl())
    normalized_url2 = normalize_url(url2.geturl())
    return normalized_url1 == normalized_url2


def get_redirect_origin(redirects, url):
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

    current_url = copy.deepcopy(url)

    # Follow the redirect chain until we reach the origin or don't find a redirect

    while True:
        redirect = None
        for r in redirects:
            if compare_urls(r["destination"], current_url):
                redirect = r
        if not redirect:
            break
        current_url = redirect["source"]

    return current_url if not compare_urls(current_url, url) else None
