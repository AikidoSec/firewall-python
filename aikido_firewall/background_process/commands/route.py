"""Exports `process_route`"""


def process_route(connection_manager, data, queue=None):
    """Called every time the user visits a route"""
    if connection_manager:
        connection_manager.routes.add_route(method=data[0], path=data[1])
