"""
Exports class Routes
"""


class Routes:
    """
    Stores all routes
    """

    def __init__(self, max_size):
        self.max_size = max_size
        self.routes = dict()

    def add_route(self, method, path):
        """
        Adds your route
        """
        key = route_to_key(method, path)

        if self.routes.get(key):
            # Route already exists, add a hit
            self.routes.get(key)["hits"] += 1
        else:
            self.manage_routes_size()
            # Add an empty route :
            self.routes[key] = {"method": method, "path": path, "hits": 1}

    def clear(self):
        """Deletes all routes"""
        self.routes = {}

    def manage_routes_size(self):
        """
        Evicts LRU routes if the size is too large
        """
        if len(self.routes) >= self.max_size:
            least_used_key = None


def route_to_key(method, path):
    """Creates a key from the method and path"""
    return f"{method}:{path}"
