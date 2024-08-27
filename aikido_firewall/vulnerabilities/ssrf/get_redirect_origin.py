"""Exports get_redirect_origin function"""

import copy
from urllib.parse import urlparse, urlunparse


def normalize_url(url):
    """Normalizes the url"""
    # Parse the URL
    parsed_url = urlparse(url)

    # Normalize components
    scheme = parsed_url.scheme.lower()  # Lowercase scheme
    netloc = parsed_url.netloc.lower()  # Lowercase netloc
    path = parsed_url.path.rstrip("/")  # Remove trailing slash
    query = parsed_url.query  # Keep query as is
    fragment = parsed_url.fragment  # Keep fragment as is

    # Remove default ports (80 for http, 443 for https)
    if scheme == "http" and parsed_url.port == 80:
        netloc = netloc.replace(":80", "")
    elif scheme == "https" and parsed_url.port == 443:
        netloc = netloc.replace(":443", "")

    # We do not care about the scheme (Isn't extracted) :
    scheme = "http"

    # Reconstruct the normalized URL
    normalized_url = urlunparse((scheme, netloc, path, "", query, fragment))
    return normalized_url


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
