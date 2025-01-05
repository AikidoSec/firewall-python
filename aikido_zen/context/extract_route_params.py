"""Exports extract_route_params function"""

from urllib.parse import quote, unquote
from aikido_zen.helpers.try_parse_url_path import try_parse_url_path
from aikido_zen.helpers.build_route_from_url import replace_url_segment_with_param


def extract_route_params(url):
    """Will try and build an array of user input based on the url"""
    results = []
    try:
        path = try_parse_url_path(url)
        segments = path.split("/")
        for segment in segments:
            segment = unquote(segment)
            if segment.isalnum():
                continue  # Ignore alphanumerical parts of the url

            if segment is not quote(segment):
                results.append(segment)  # This is not a standard piece of the URL
            elif replace_url_segment_with_param(segment) is not segment:
                results.append(segment)  # Might be a secret, a hash, ...

        if len(results) > 0 or "." in unquote(path):
            # There are already phishy parts of the url OR
            # urldecoded path contains dots, which is uncommon and could point to path traversal.
            results.append(path[1:])  # Add path after slash as user input

    except Exception:
        pass
    return results
