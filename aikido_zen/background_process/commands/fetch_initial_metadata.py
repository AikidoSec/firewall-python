"""Exports `process_fetch_initial_metadata`"""

ANALYSIS_ON_FIRST_X_ROUTES = 20


def process_fetch_initial_metadata(connection_manager, data, queue=None):
    """
    Fetches initial metadata, also adds request statistic (Optimized)
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
    if route:
        route_hits = route.get("hits", 0)
        if route_hits > ANALYSIS_ON_FIRST_X_ROUTES:
            # As an optimization, after the analysis is done using the ROUTE command,
            # This IPC Command takes over in adding the hits.
            connection_manager.routes.add_route(route_metadata)

    return {
        "bypassed_ips": bypassed_ips,
        "matched_endpoints": matched_endpoints,
        "hits": route_hits,
    }
