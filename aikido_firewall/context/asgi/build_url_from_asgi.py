"""Exports `build_url_from_asgi`"""


def build_url_from_asgi(scope):
    """Builds a URL from the different parts of the ASGI scope"""
    scheme = scope["scheme"]

    server = scope["server"]
    if not server:
        return
    # server[0] : Host, server[1] : Port
    host = f"{server[0]}:{server[1]}"

    root_path = scope.get("root_path", "")
    path = scope.get("path", "")
    uri = path.replace(root_path, "", 1)
    return f"{scheme}://{host}{uri}"
