"""Exports extract_route_params function"""

from urllib.parse import unquote
from aikido_zen.helpers.try_parse_url_path import try_parse_url_path


def extract_route_params(url):
    """Will try and build an array of user input based on the url"""
    results = []
    path = try_parse_url_path(url)
    segments = path.split("/")
    for segment in segments:
        if segment.isalnum():
            continue  # Ignore alphanumerical parts of the url
        unqouted_segment = unquote(segment)
        if segment is not unqouted_segment:
            # URL Encoded part, see this as user input
            results.append(unqouted_segment)
    return results
