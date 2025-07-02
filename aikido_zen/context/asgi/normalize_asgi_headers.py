"""Mainly exports normalize_asgi_headers"""

from aikido_zen.helpers.headers import Headers


def normalize_asgi_headers(headers) -> Headers:
    """
    Normalizes headers provided by ASGI :
    Decodes them, uppercase and underscore keys
    """
    result = Headers()
    for k, v in headers:
        result.store_header(k.decode("utf-8"), v.decode("utf-8"))
    return result
