"""Exports `process_fetch_initial_metadata`"""


def process_fetch_initial_metadata(reporter, data, conn, queue=None):
    """Fetches initial metadata"""
    if not reporter:
        return conn.send({"bypassed_ips": [], "matched_endpoints": []})
    route_metadata = data["route_metadata"]
    bypassed_ips = reporter.conf.bypassed_ips
    matched_endpoints = reporter.conf.get_endpoints(route_metadata)
    conn.send(
        {
            "bypassed_ips": bypassed_ips,
            "matched_endpoints": matched_endpoints,
        }
    )
