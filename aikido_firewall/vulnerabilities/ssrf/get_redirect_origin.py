"""Exports get_redirect_origin function"""

import copy


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
        redirect = next(
            # url.href contains the full URL so we can use it for comparison
            (r for r in redirects if r["destination"]["href"] == current_url["href"]),
            None,
        )
        if not redirect:
            break
        current_url = redirect["source"]

    return current_url["href"] if current_url["href"] != url["href"] else None
