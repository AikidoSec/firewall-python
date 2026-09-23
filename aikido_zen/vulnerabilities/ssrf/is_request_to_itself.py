from aikido_zen.helpers.get_trusted_hostnames import get_trusted_hostnames


def is_request_to_itself(outbound_hostname):
    """
    We don't want to block outgoing requests to hostnames that are explicitly
    declared as the server itself via AIKIDO_TRUSTED_HOSTNAMES. Customers must explicitly list their own hostnames in
    the AIKIDO_TRUSTED_HOSTNAMES environment variable (comma-separated).
    """
    if not outbound_hostname or not isinstance(outbound_hostname, str):
        return False

    trusted = get_trusted_hostnames()
    return outbound_hostname in trusted
