"""Exports `process_initialize_route`"""


def process_initialize_route(connection_manager, data, queue=None):
    """
    This is called the first time a route is discovered to initialize it and add one hit.
    data is a dictionary called route_metadata which includes: route, method and url.
    """
    if connection_manager:
        connection_manager.routes.initialize_route(route_metadata=data)
        connection_manager.routes.increment_route(route_metadata=data)
