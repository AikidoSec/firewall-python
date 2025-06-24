from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.helpers.logging import logger


class Routes:
    """
    Stores: method & path for a given route, hit counts, the generated api spec.
    """

    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.routes = {}

    def get(self, method, route):
        key = route_to_key(method, route)
        return self.routes.get(key)

    def ensure_route(self, method, route):
        if self.get(method, route):
            return  # A route already exists
        key = route_to_key(method, route)
        self.routes[key] = {
            "method": method,
            "path": route,
            "hits": 0,
            "apispec": {},
        }
        logger.error(self.routes)
        self.manage_routes_size()

    def increment_route(self, method, route):
        self.ensure_route(method, route)
        self.get(method, route)["hits"] += 1

    def update_route_with_apispec(self, method, route, apispec):
        self.ensure_route(method, route)
        update_route_info(apispec, self.get(method, route))

    def export(self, include_apispecs=True):
        result = dict(self.routes)
        if not include_apispecs:
            for route in result.values():
                route["apispec"] = {}
        return result

    def import_from_record(self, new_routes):
        if not isinstance(new_routes, dict):
            return
        for route in new_routes.values():
            self.ensure_route(method=route["method"], route=route["path"])
            existing_route = self.get(method=route["method"], route=route["path"])
            # merge
            existing_route["hits"] += route.get("hits", 0)
            update_route_info(route.get("apispec", {}), existing_route)
        self.manage_routes_size()

    def clear(self):
        self.routes = {}

    def empty(self):
        return len(self.routes) == 0

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


def route_to_key(method, route):
    return f"{method}:{route}"
