"""Mainly exports normalize_asgi_headers"""


def normalize_asgi_headers(headers):
    """
    Normalizes headers provided by ASGI :
    Decodes them, uppercase and underscore keys
    """
    parsed_headers = {}
    for k, v in headers:
        # Normalizing key : decoding, removing dashes and uppercase
        key_without_dashes = k.decode("utf-8").replace("-", "_")
        key_normalized = key_without_dashes.upper()
        parsed_headers[key_normalized] = v.decode("utf-8")
    return parsed_headers
