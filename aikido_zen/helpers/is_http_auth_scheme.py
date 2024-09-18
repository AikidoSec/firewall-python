"""Exports is_http_auth_scheme function"""

AUTH_SCHEMES = [
    "basic",
    "bearer",
    "digest",
    "dpop",
    "gnap",
    "hoba",
    "mutual",
    "negotiate",
    "privatetoken",
    "scram-sha-1",
    "scram-sha-256",
    "vapid",
]


def is_http_auth_scheme(scheme):
    """
    Checks if a string is a valid HTTP authentication scheme.
    https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml
    """
    return scheme.lower() in AUTH_SCHEMES
