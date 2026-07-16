"""Export Hostnames class"""

import socket


class Hostnames:
    """Stores hostnames"""

    def __init__(self, max_entries=200):
        self.max_entries = max_entries
        self.map = {}

    def add(self, hostname, port, hits=1):
        """Add a hostname and port to the map"""
        normalized_port = normalize_port(port)
        key = get_key(hostname, normalized_port)
        if not self.map.get(key):
            self.map[key] = {"hostname": hostname, "port": normalized_port, "hits": 0}
        if len(self.map) > self.max_entries:
            # Remove the first added hostname
            first_added = next(iter(self.map))
            del self.map[first_added]
        self.map[key]["hits"] += hits

    def as_array(self):
        """Exports the contents as an array"""
        return list(self.map.values())

    def clear(self):
        """Clear the entire map"""
        self.map.clear()


def get_key(hostname, port):
    """Returns a string key"""
    return f"{hostname}:{port}"


def normalize_port(port):
    """
    Ensures port is an int (or None), never a str.
    `socket.getaddrinfo` accepts a service name (e.g. "http") or a numeric
    string as the port, so it needs to be resolved/parsed to a number here.
    """
    if port is None or isinstance(port, int):
        return port
    try:
        return int(port)
    except (TypeError, ValueError):
        pass
    try:
        return socket.getservbyname(port)
    except OSError:
        return None
