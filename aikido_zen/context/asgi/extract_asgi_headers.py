"""Mainly exports extract_asgi_headers"""

from aikido_zen.helpers.headers import Headers


def extract_asgi_headers(headers) -> Headers:
    result = Headers()
    for k, v in headers:
        result.store_header(k.decode("utf-8"), v.decode("utf-8"))
    return result
