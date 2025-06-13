from aikido_zen.api_discovery.update_route_info import update_route_info
from .route_to_key import route_to_key


class Routes:
    """
    Stores: method & path for a given route, hit counts, the generated api spec.
    """

    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.routes = {}

    def get(self, route_metadata):
        key = route_to_key(route_metadata)
        return self.routes[key]

    def ensure_route(self, route_metadata=None, key=None):
        if self.get(route_metadata):
            return  # A route already exists
        if key is None:
            key = route_to_key(route_metadata)
        self.routes[key] = {
            "method": route_metadata.get("method"),
            "path": route_metadata.get("route"),
            "hits": 0,
            "apispec": {},
        }
        self.manage_routes_size()

    def increment_route(self, route_metadata):
        self.ensure_route(route_metadata)
        self.get(route_metadata)["hits"] += 1

    def update_route_with_apispec(self, route_metadata, apispec):
        self.ensure_route(route_metadata)
        update_route_info(apispec, self.get(route_metadata))

    def export(self):
        return dict(self.routes)

    def import_from_record(self, new_routes):
        for key, route in new_routes:
            self.ensure_route(key=key)
            existing_route = self.routes.get(key)
            # merge
            existing_route["hits"] += route.get("hits", 0)
            update_route_info(route.get("apispec", {}), existing_route)

    def clear(self):
        """Deletes all routes"""
        self.routes = {}

    def manage_routes_size(self):
        """
        Evicts LRU routes if the size is too large
        """
        if len(self.routes) > self.max_size:
            least_used = [None, float("inf")]
            for key, route in self.routes.items():
                if route.get("hits") < least_used[1]:
                    least_used = [key, route.get("hits")]
            if least_used[0]:
                del self.routes[least_used[0]]
