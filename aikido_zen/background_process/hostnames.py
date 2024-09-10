"""Export Hostnames class"""


class Hostnames:
    """Stores hostnames"""

    def __init__(self, max_entries=200):
        self.max_entries = max_entries
        self.map = {}

    def add(self, hostname, port):
        """Add a hostname and port to the map"""
        if hostname in self.map:
            return

        if len(self.map) >= self.max_entries:
            # Remove the first added hostname
            first_added = next(iter(self.map))
            del self.map[first_added]

        self.map[hostname] = port

    def as_array(self):
        """Exports the contents as an array"""
        return [
            {"hostname": hostname, "port": port} for hostname, port in self.map.items()
        ]

    def clear(self):
        """Clear the entire map"""
        self.map.clear()
