"""Exports route_to_key function"""


def route_to_key(route_metadata):
    """Creates a key from the method and path"""
    method = route_metadata.get("method")
    route = route_metadata.get("route")
    return f"{method}:{route}"
