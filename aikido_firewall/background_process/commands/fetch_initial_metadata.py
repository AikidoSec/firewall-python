"""Exports `process_fetch_initial_metadata`"""


def process_fetch_initial_metadata(reporter, data, queue=None):
    """Fetches initial metadata"""
    if not reporter:
        return {"bypassed_ips": [], "matched_endpoints": []}
    route_metadata = data["route_metadata"]
    bypassed_ips = reporter.conf.bypassed_ips
    matched_endpoints = reporter.conf.get_endpoints(route_metadata)
    return {
        "bypassed_ips": bypassed_ips,
        "matched_endpoints": matched_endpoints,
    }
