"""Exports `process_fetch_initial_metadata`"""


def process_fetch_initial_metadata(bg_process, data, conn):
    """Fetches initial metadata"""
    route_metadata = data["route_metadata"]
    bypassed_ips = bg_process.reporter.conf.bypassed_ips
    matched_endpoints = bg_process.reporter.conf.get_endpoints(route_metadata)
    conn.send(
        {
            "bypassed_ips": bypassed_ips,
            "matched_endpoints": matched_endpoints,
        }
    )
