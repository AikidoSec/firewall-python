"""Exports `build_url_from_wsgi`"""


def build_url_from_wsgi(request):
    """Builds a URL from the different parts in a WSGI request"""
    scheme = request["wsgi.url_scheme"]
    host = request["HTTP_HOST"]
    uri = request["PATH_INFO"]
    return f"{scheme}://{host}{uri}"
