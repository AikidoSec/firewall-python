"""Exports `process_should_ratelimit`"""

import aikido_zen.ratelimiting as ratelimiting


def process_should_ratelimit(connection_manager, data, queue=None):
    """
    Called to check if the context passed along as data should be rate limited
    data object should be a dict including route_metadata, remote_address and user
    route_metadata object includes route, url and method
    """
    if not connection_manager:
        return False
    return ratelimiting.should_ratelimit_request(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        connection_manager=connection_manager,
    )
