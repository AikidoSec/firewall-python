"""Exports `process_fetch_initial_metadata`"""


def process_fetch_initial_metadata(connection_manager, data, conn, queue=None):
    """Fetches initial metadata"""
    if not connection_manager:
        return conn.send({"bypassed_ips": [], "matched_endpoints": []})
    route_metadata = data["route_metadata"]
    bypassed_ips = connection_manager.conf.bypassed_ips
    matched_endpoints = connection_manager.conf.get_endpoints(route_metadata)
    conn.send(
        {
            "bypassed_ips": bypassed_ips,
            "matched_endpoints": matched_endpoints,
        }
    )
