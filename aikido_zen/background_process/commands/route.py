"""Exports `process_route`"""


def process_route(connection_manager, data, queue=None):
    """
    Called every time the user visits a route
    data is a dictionary with "route_metadata" and an optional attribute "apispec"
    """
    if connection_manager:
        route_metadata = data.get("route_metadata")
        connection_manager.routes.add_route(route_metadata)
        if data.get("apispec"):
            connection_manager.routes.update_route_with_apispec(
                route_metadata, data.get("apispec")
            )
