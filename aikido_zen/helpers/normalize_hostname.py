def normalize_hostname(hostname):
    if not hostname or not isinstance(hostname, str):
        return hostname

    # Lowercase and strip trailing dot (DNS resolvers may return FQDNs like "example.com.")
    result = hostname.lower().rstrip(".")

    try:
        # Decode Punycode if the hostname starts with xn--
        if result.startswith("xn--"):
            result = result.encode("ascii").decode("idna")
        return result
    except (UnicodeError, LookupError):
        return result
