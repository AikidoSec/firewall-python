"""Helper function file `is_localhost_ip`"""


def is_localhost_ip(ip):
    """Checks if the ip is a local ip"""
    return ip in ["127.0.0.1", "::ffff:127.0.0.1", "::1"]
