"""
Includes try_parse_url which will try and parse
a url using urlparse.
Includes try_parse_url_path
"""

from urllib.parse import urlparse


def try_parse_url(url):
    """try to parse Url with urlparse"""
    try:
        return urlparse(url)
    except ValueError:
        return None


def try_parse_url_path(url):
    """Try and parse url path"""
    parsed = try_parse_url(f"http://localhost{url}" if url.startswith("/") else url)

    if not parsed or not parsed.scheme:
        return None
    if parsed.path == "":
        return "/"
    return parsed.path
