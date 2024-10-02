"""
Exports class Routes
"""

from aikido_zen.helpers.logging import logger
from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.api_discovery.get_api_info import get_api_info


class Routes:
    """
    Stores all routes
    """

    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.routes = {}

    def add_route(self, route_metadata):
        """
        Adds your route
        route_metadata object includes route, url and method
        """
        method, path = route_metadata.get("method"), route_metadata.get("route")
        key = route_to_key(method, path)

        if self.routes.get(key):
            # Route already exists, add a hit
            route = self.routes.get(key)
            route["hits"] += 1
        else:
            self.manage_routes_size()
            # Add an empty route :
            self.routes[key] = {
                "method": method,
                "path": path,
                "hits": 1,
                "apispec": {},
            }

    def update_route_with_apispec(self, route_metadata, apispec):
        """
        Updates apispec of a given route (or creates it).
        route_metadata object includes route, url and method
        """
        key = route_to_key(route_metadata.get("method"), route_metadata.get("route"))
        if not self.routes.get(key):
            return
        update_route_info(apispec, self.routes[key])

    def clear(self):
        """Deletes all routes"""
        self.routes = {}

    def manage_routes_size(self):
        """
        Evicts LRU routes if the size is too large
        """
        if len(self.routes) >= self.max_size:
            least_used = [None, float("inf")]
            for key, route in self.routes.items():
                if route.get("hits") < least_used[1]:
                    least_used = [key, route.get("hits")]
            if least_used[0]:
                del self.routes[least_used[0]]

    def __iter__(self):
        return iter(self.routes.values())

    def __len__(self):
        return len(self.routes)


def route_to_key(method, path):
    """Creates a key from the method and path"""
    return f"{method}:{path}"
