"""Mainly exports normalize_asgi_headers"""

from aikido_zen.helpers.headers import Headers


def normalize_asgi_headers(headers) -> Headers:
    """
    Normalizes headers provided by ASGI :
    Decodes them, uppercase and underscore keys
    """
    result = Headers()
    for k, v in headers:
        result.store_headers(k.decode("latin-1"), decoded_header_values(v))
    return result


def decoded_header_values(raw):
    """
    latin-1 stays last because get_header returns the last value.
    The UTF-8 value is included because an app may decode the header
    again before a sink.
    """
    as_framework = raw.decode("latin-1")
    try:
        as_utf8 = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [as_framework]
    if as_utf8 == as_framework:
        return [as_framework]
    return [as_utf8, as_framework]
