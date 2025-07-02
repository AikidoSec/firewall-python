from dataclasses import dataclass
from typing import Dict, List
from urllib.parse import parse_qs
from aikido_zen.helpers.get_ip_from_request import get_ip_from_request
from ..parse_cookies import parse_cookies
from .extract_asgi_headers import extract_asgi_headers
from .build_url_from_asgi import build_url_from_asgi


@dataclass
class ASGIContext:
    method: str
    headers: Dict[str, List[str]]
    cookies: dict
    url: str
    query: dict
    remote_address: str


def parse_asgi_scope(scope) -> ASGIContext:
    """
    This extracts ASGI Scope attributes, described in :
    https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope
    """
    headers = extract_asgi_headers(scope["headers"])

    cookies = {}
    if "COOKIE" in headers and headers["COOKIE"]:
        cookies = parse_cookies(headers["COOKIE"][-1])

    raw_ip = scope["client"][0] if scope["client"] else ""
    remote_address = get_ip_from_request(raw_ip, headers)

    return ASGIContext(
        method=scope["method"],
        headers=headers,
        cookies=cookies,
        url=build_url_from_asgi(scope),
        query=parse_qs(scope["query_string"].decode("utf-8")),
        remote_address=remote_address,
    )
