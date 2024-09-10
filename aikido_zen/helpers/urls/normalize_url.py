"""Helper function file, exports normalize_url"""

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

    # Reconstruct the normalized URL
    normalized_url = urlunparse((scheme, netloc, path, "", query, fragment))
    return normalized_url
