"""
Includes try_parse_url which will try and parse
a url using urlparse.
Includes try_parse_url_path
"""

from urllib.parse import urlparse
import regex as re


def try_parse_url(url):
    """try to parse Url with urlparse"""
    try:
        return urlparse(url)
    except ValueError:
        return None


def try_parse_url_path(url):
    """Try and parse url path"""
    if not url:
        return None

    parsed = try_parse_url(f"http://localhost{url}" if url.startswith("/") else url)

    if not parsed or not parsed.scheme:
        return None
    if parsed.path == "":
        return "/"

    normalized_path = parsed.path
    if "//" in normalized_path:
        # Multiple slashes are ignored in python, so we want to also remove them here
        # This allows the route building & endpoint matching to work properly.
        normalized_path = re.sub(r"/+", "/", normalized_path)

    return normalized_path
