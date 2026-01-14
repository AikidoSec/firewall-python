def normalize_hostname(hostname):
    if not hostname or not isinstance(hostname, str):
        return hostname

    result = hostname
    try:
        # Check if hostname contains punycode (starts with xn--)
        if hostname.startswith("xn--"):
            result = hostname.encode("ascii").decode("idna")

        return result
    except (UnicodeError, LookupError):
        # If decoding fails, return original hostname
        return hostname
