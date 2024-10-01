"""Export Hostnames class"""


class Hostnames:
    """Stores hostnames"""

    def __init__(self, max_entries=200):
        self.max_entries = max_entries
        self.map = {}

    def add(self, hostname, port):
        """Add a hostname and port to the map"""
        key = get_key(hostname, port)
        if not self.map.get(key):
            self.map[key] = {"hostname": hostname, "port": port, "hits": 0}
        if len(self.map) > self.max_entries:
            # Remove the first added hostname
            first_added = next(iter(self.map))
            del self.map[first_added]
        self.map[key]["hits"] += 1

    def as_array(self):
        """Exports the contents as an array"""
        return list(self.map.values())

    def clear(self):
        """Clear the entire map"""
        self.map.clear()


def get_key(hostname, port):
    """Returns a string key"""
    return f"{hostname}:{port}"
