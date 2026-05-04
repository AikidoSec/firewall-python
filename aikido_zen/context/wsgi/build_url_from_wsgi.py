"""Exports `build_url_from_wsgi`"""


def build_url_from_wsgi(request):
    """Builds a URL from the different parts in a WSGI request"""
    scheme = request["wsgi.url_scheme"]
    uri = request["PATH_INFO"]

    host = ""
    if "HTTP_HOST" not in request or request["HTTP_HOST"] == "":
        host = request["SERVER_NAME"]
        port = request["SERVER_PORT"]

        host = f"{host}:{port}"
    else:
        host = request["HTTP_HOST"]

    query_string = request.get("QUERY_STRING", "")
    if query_string:
        uri = f"{uri}?{query_string}"

    return f"{scheme}://{host}{uri}"
