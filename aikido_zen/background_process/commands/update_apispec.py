"""Exports `process_update_apispec`"""


def process_update_apispec(connection_manager, data, queue=None):
    """
    Called every time the user visits a route
    data is a dictionary with "route_metadata" and "apispec"
    """
    if connection_manager and data.get("apispec") and data.get("route_metadata"):
        route_metadata = data.get("route_metadata")
        connection_manager.routes.update_route_with_apispec(
            route_metadata, data.get("apispec")
        )
