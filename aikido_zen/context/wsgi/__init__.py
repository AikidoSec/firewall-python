from dataclasses import dataclass
from typing import Dict, List
from urllib.parse import parse_qs
from aikido_zen.helpers.get_ip_from_request import get_ip_from_request
from .extract_wsgi_headers import extract_wsgi_headers
from .build_url_from_wsgi import build_url_from_wsgi
from ..parse_cookies import parse_cookies


@dataclass
class WSGIContext:
    method: str
    headers: Dict[str, List[str]]
    cookies: dict
    url: str
    query: dict
    remote_address: str


def parse_wsgi_environ(environ) -> WSGIContext:
    """
    This extracts WSGI attributes, described in :
    https://peps.python.org/pep-3333/#environ-variables
    """
    headers: Dict[str, List[str]] = extract_wsgi_headers(environ)
    # Content type is generally not included as a header, do include this as a header to simplify :
    if "CONTENT_TYPE" in environ:
        headers["CONTENT_TYPE"] = [environ["CONTENT_TYPE"]]

    cookies = {}
    if "COOKIE" in headers and headers["COOKIE"]:
        cookies = parse_cookies(headers["COOKIE"][-1])

    return WSGIContext(
        method=environ["REQUEST_METHOD"],
        headers=headers,
        cookies=cookies,
        url=build_url_from_wsgi(environ),
        query=parse_qs(environ["QUERY_STRING"]),
        remote_address=get_ip_from_request(environ["REMOTE_ADDR"], headers),
    )
