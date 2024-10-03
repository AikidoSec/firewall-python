"""Exports `process_fetch_initial_metadata`"""


def process_fetch_initial_metadata(connection_manager, data, queue=None):
    """
    Fetches initial metadata and :
    - Increments the total requests statistic.
    - If a route exists, increments it's hits.
    """
    if not connection_manager:
        return {"bypassed_ips": [], "matched_endpoints": []}
    if connection_manager.statistics:
        # Update request statistic for an optimization.
        connection_manager.statistics.requests["total"] += 1
    route_metadata = data["route_metadata"]

    bypassed_ips = connection_manager.conf.bypassed_ips
    matched_endpoints = connection_manager.conf.get_endpoints(route_metadata)

    route_hits = 0
    route = connection_manager.routes.get(route_metadata)
    if route and route.get("hits") is not None:
        # As an optimization after the route gets initialized (see ./initialize_route.py),
        # The route hits get added here so you don't have to keep sending two IPC commands.
        route_hits = route.get("hits", 0)
        # We only increment hits after getting them, so if it's the 2nd request, the hit count is still 1.
        connection_manager.routes.increment_route(route_metadata)
    return {
        "bypassed_ips": bypassed_ips,
        "matched_endpoints": matched_endpoints,
        "hits": route_hits,
    }
