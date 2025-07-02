"""Exports function extract_wsgi_headers"""

from aikido_zen.helpers.headers import Headers


def extract_wsgi_headers(request) -> Headers:
    """Extracts WSGI headers which start with HTTP_ from request dict"""
    headers = Headers()
    for key, value in request.items():
        if key.startswith("HTTP_"):
            # Remove the 'HTTP_' prefix and store in the headers dictionary
            header_key = key[5:]
            headers.store_header(header_key, value)
    return headers
