from typing import Optional, List, Tuple

from aikido_zen.helpers.get_port_from_url import get_port_from_url
from aikido_zen.helpers.try_parse_url import try_parse_url


def normalize_string_to_hostname_and_port(
    input: str,
) -> List[Tuple[str, Optional[int]]]:
    result = []
    variants = [
        input,
        f"http://{input}",
        f"https://{input}",
        f"http://[{input}]",
        f"https://[{input}]",
    ]
    for variant_raw_url in variants:
        parsed_url = try_parse_url(variant_raw_url)
        if parsed_url is None:
            continue
        if parsed_url.hostname is None:
            continue

        # Important to lowercase!
        hostname = parsed_url.hostname.lower()
        port = get_port_from_url(parsed_url.geturl())

        result.append((hostname, port))

    return result
