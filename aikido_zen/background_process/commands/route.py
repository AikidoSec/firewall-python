"""Exports `process_route`"""


def process_route(connection_manager, data, queue=None):
    """
    Called every time the user visits a route
    data is a context object, so we can extract api routes.
    """
    if connection_manager:
        connection_manager.routes.add_route(context=data)
