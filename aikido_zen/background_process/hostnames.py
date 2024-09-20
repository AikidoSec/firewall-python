"""Export Hostnames class"""


class Hostnames:
    """Stores hostnames"""

    def __init__(self, max_entries=200):
        self.max_entries = max_entries
        self.map = {}

    def add(self, hostname, port):
        """Add a hostname and port to the map"""
        if self.length >= self.max_entries:
            # Remove the first added hostname
            first_added = next(iter(self.map))
            ports = self.map[
                first_added
            ]  # Get the Ports object associated with the first key

            if len(ports) > 1:
                first_port = next(iter(ports))
                ports.remove(first_port)
            else:
                del self.map[first_added]
        if not self.map.get(hostname):
            self.map[hostname] = set()
        self.map[hostname].add(port)

    @property
    def length(self):
        """Gives length with ports as seperate entities"""
        return sum(len(ports) for ports in self.map.values())

    def as_array(self):
        """Exports the contents as an array"""
        return [
            {"hostname": hostname, "port": port}
            for hostname, ports in self.map.items()
            for port in ports
        ]

    def clear(self):
        """Clear the entire map"""
        self.map.clear()
