from typing import List
from aikido_zen.helpers.try_parse_url import try_parse_url


def get_hostname_options(raw_hostname: str) -> List[str]:
    options_urls = [try_parse_url(f"http://{raw_hostname}")]

    # Add a case for hostnames like ::1 or ::ffff:127.0.0.1, who need brackets to be parsed
    options_urls.append(try_parse_url(f"http://[{raw_hostname}]"))

    # Add a case when the hostname is in punycode (like xn--pp-oia.aikido.dev)
    if "xn--" in raw_hostname:
        try:
            hostname_decoded = raw_hostname.encode("ascii", errors="").decode("idna")
        except UnicodeError:
            # Malformed punycode (e.g. xn--a.attacker.com): keep the raw form only,
            # so the SSRF scan still runs against the requested hostname instead
            # of aborting with an exception.
            hostname_decoded = None
        if hostname_decoded:
            options_urls.append(try_parse_url(f"http://{hostname_decoded}"))

    # Map to url.hostname, deduplicating (bracketed and unbracketed
    # variants can resolve to the same hostname depending on Python version)
    options = []
    for options_url in options_urls:
        if options_url and options_url.hostname and options_url.hostname not in options:
            options.append(options_url.hostname)
    return options
