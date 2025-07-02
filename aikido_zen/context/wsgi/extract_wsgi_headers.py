"""Exports function extract_wsgi_headers"""

from typing import Dict, List


def extract_wsgi_headers(request) -> Dict[str, List[str]]:
    """Extracts WSGI headers which start with HTTP_ from request dict"""
    headers = {}
    for key, value in request.items():
        if key.startswith("HTTP_"):
            # Remove the 'HTTP_' prefix and store in the headers dictionary
            headers[key[5:]] = [value]
    return headers
