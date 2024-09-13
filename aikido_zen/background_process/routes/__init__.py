"""
Exports class Routes
"""

from aikido_zen.api_discovery.update_body_info import update_body_info
from aikido_zen.api_discovery.get_body_info import get_body_info

ANALYSIS_ON_FIRST_X_ROUTES = 20


class Routes:
    """
    Stores all routes
    """

    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.routes = {}

    def add_route(self, context):
        """
        Adds your route
        """
        method, path = context.method, context.path
        key = route_to_key(method, path)

        if self.routes.get(key):
            # Route already exists, add a hit
            route = self.routes.get(key)
            route["hits"] += 1
            if route["hits"] <= ANALYSIS_ON_FIRST_X_ROUTES:
                # Only analyze the first x routes for api discovery
                route["body"] = update_body_info(context, route["body"])
        else:
            self.manage_routes_size()
            # Add an empty route :
            self.routes[key] = {
                "method": method,
                "path": path,
                "hits": 1,
                "body": get_body_info(context),
            }

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
