"""Exports get_redirect_origin"""

from aikido_zen.helpers.urls.normalize_url import normalize_url


def get_redirect_origin(redirects, hostname, port):
    """
    This function checks if the given URL is part of a redirect chain that is passed in the redirects parameter.
    It returns the origin of a redirect chain if the URL is the result of a redirect.
    The origin is the first URL in the chain, so the initial URL that was requested and redirected
    to the given URL or, in the case of multiple redirects, the URL that was redirected to the given URL.

    Example:
    Redirect chain: A -> B -> C: get_redirect_origin([A -> B, B -> C], C) => A
                               : get_redirect_origin([A -> B, B -> C], B) => A
                               : get_redirect_origin([A -> B, B -> C], D) => None
    """
    if not isinstance(redirects, list):
        return None

    visited = set()
    current_urls = find_url_matching_hostname_and_port(hostname, port, redirects)
    for url in current_urls:
        origin = find_origin(redirects, url, visited)
        if origin and not compare_urls(origin, url):
            # If origin exists and it's different return
            return origin


def find_origin(redirects, url, visited):
    """Recursive function that traverses the redirects"""
    if url is None or url.geturl() in visited:
        # To avoid infinite loops in case of cyclic redirects
        return url

    visited.add(url.geturl())

    # Find a redirect where the current URL is the destination
    redirect = next((r for r in redirects if compare_urls(r["destination"], url)), None)
    if redirect:
        # Recursively find the origin starting from the source URL
        return find_origin(redirects, redirect["source"], visited)

    # If no redirect leads to this URL, return the URL itself
    return url


def compare_urls(dst, src):
    """Compares normalized URLs."""
    normalized_dst = normalize_url(dst.geturl())
    normalized_src = normalize_url(src.geturl())
    return normalized_dst == normalized_src


def find_url_matching_hostname_and_port(hostname, port, redirects):
    """Finds the initial url to start with (the one matching hostname and port)"""
    urls = []
    for redirect in redirects:
        r_port = redirect["destination"].port
        if r_port and r_port != port:
            continue
        if redirect["destination"].hostname != hostname:
            continue
        urls.append(redirect["destination"])
    return urls
