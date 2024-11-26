"""Exports process_renew_config"""

from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.helpers.logging import logger


def process_sync_data(connection_manager, data, conn, queue=None):
    """
    Synchronizes data between the thread-local cache (with a TTL of usually 1 minute) and the
    background thread. Which data gets synced?
    Thread -> BG Process : Hits, request statistics, api specs
    BG Process -> Thread : Routes, endpoints, bypasssed ip's, blocked users
    """
    routes = connection_manager.routes
    for route in data.get("current_routes", {}).values():
        route_metadata = {"method": route["method"], "route": route["path"]}
        if not routes.get(route_metadata):
            routes.initialize_route(route_metadata)
        existing_route = routes.get(route_metadata)

        # Update hit count :
        hits_delta_since_sync = int(route.get("hits_delta_since_sync", 0))
        existing_route["hits"] += hits_delta_since_sync

        # Update API Spec :
        update_route_info(route["apispec"], existing_route)

    connection_manager.statistics.requests["total"] += data.get("reqs", 0)

    return {
        "routes": dict(connection_manager.routes.routes),
        "endpoints": connection_manager.conf.endpoints,
        "bypassed_ips": connection_manager.conf.bypassed_ips,
        "blocked_uids": connection_manager.conf.blocked_uids,
    }
