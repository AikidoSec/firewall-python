from aikido_zen.helpers.get_ip_from_request import trust_proxy
from aikido_zen.helpers.get_port_from_url import get_port_from_url
from aikido_zen.helpers.try_parse_url import try_parse_url


def is_request_to_itself(server_url, outbound_hostname, outbound_port):
    """
    We don't want to block outgoing requests to the same host as the server
    (often happens that we have a match on headers like `Host`, `Origin`, `Referer`, etc.)
    We have to check the port as well, because the hostname can be the same but with a different port
    """

    # When the app is not behind a reverse proxy, we can't trust the hostname inside `server_url`
    # The hostname in `server_url` is built from the request headers
    # The headers can be manipulated by the client if the app is directly exposed to the internet
    if not trust_proxy():
        return False

    base_url = try_parse_url(server_url)
    if base_url is None:
        return False

    if base_url.hostname != outbound_hostname:
        return False

    base_url_port = get_port_from_url(base_url, parsed=True)

    # If the port and hostname are the same, the server is making a request to itself
    if base_url_port == outbound_port:
        return True

    # Special case for HTTP/HTTPS ports
    # In production, the app will be served on port 80 and 443
    if base_url_port == 80 and outbound_port == 443:
        return True
    if base_url_port == 443 and outbound_port == 80:
        return True

    return False
