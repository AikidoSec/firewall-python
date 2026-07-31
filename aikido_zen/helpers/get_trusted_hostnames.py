"""Helper function file, see function docstring"""

import os


def get_trusted_hostnames():
    """
    Parses the AIKIDO_TRUSTED_HOSTNAMES environment variable.
    Returns a list of hostnames that should be considered as the server itself
    (i.e. outgoing requests to these hosts will not be flagged as SSRF).
    The value is expected to be a comma-separated list of hostnames, e.g.:
        AIKIDO_TRUSTED_HOSTNAMES=myapp.com,api.myapp.com
    """
    env_value = os.getenv("AIKIDO_TRUSTED_HOSTNAMES")
    if not env_value:
        return []
    return [h.strip() for h in env_value.split(",") if h.strip()]
