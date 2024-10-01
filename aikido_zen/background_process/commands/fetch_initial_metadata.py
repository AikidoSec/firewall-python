"""Exports `process_fetch_initial_metadata`"""


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
    return {
        "bypassed_ips": bypassed_ips,
        "matched_endpoints": matched_endpoints,
    }
