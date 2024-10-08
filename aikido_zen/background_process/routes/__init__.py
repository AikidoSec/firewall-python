"""
Exports class Routes
"""

from aikido_zen.helpers.logging import logger
from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.api_discovery.get_api_info import get_api_info
from .route_to_key import route_to_key


class Routes:
    """
    Stores all routes
    """

    def __init__(self, max_size=1000, in_thread=False):
        self.max_size = max_size
        self.routes = {}
        self.in_thread = in_thread

    def initialize_route(self, route_metadata=None, key=None):
        """
        Initializes a route for the first time.
        """
        self.manage_routes_size()
        if route_metadata:
            key = route_to_key(route_metadata)
        if self.routes.get(key):
            return
        self.routes[key] = {
            "method": route_metadata.get("method"),
            "path": route_metadata.get("route"),
            "hits": 0,
            "apispec": {},
        }
        if self.in_thread:
            self.routes[key]["thread_hits"] = 0

    def increment_route(self, route_metadata):
        """
        Adds a hit to the route (if it exists) specified in route_metadata.
        route_metadata object includes route, url and method
        """
        key = route_to_key(route_metadata)
        if not self.routes.get(key):
            return
        # Add a hit to the route :
        route = self.routes.get(key)
        route["hits"] += 1
        if self.in_thread:
            if not route.get("thread_hits"):
                route["thread_hits"] = 0
            route["thread_hits"] += 1

    def update_route_with_apispec(self, route_metadata, apispec):
        """
        Updates apispec of a given route (or creates it).
        route_metadata object includes route, url and method
        """
        key = route_to_key(route_metadata)
        if not self.routes.get(key):
            return
        update_route_info(apispec, self.routes[key])

    def get(self, route_metadata=None, key=None):
        """Gets you the route entry if it exists using route metadata"""
        if route_metadata:
            key = route_to_key(route_metadata)
        return self.routes.get(key)

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
