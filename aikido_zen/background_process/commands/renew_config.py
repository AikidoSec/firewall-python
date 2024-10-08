"""Exports process_renew_config"""

from aikido_zen.api_discovery.update_route_info import update_route_info


def process_renew_config(connection_manager, data, conn, queue=None):
    """Fetches all config data needed for thread-local cache"""

    # Process data here.
    routes = connection_manager.routes
    for route in data.values():
        route_metadata = {"method": route["method"], "route": route["path"]}
        if not routes.get(route_metadata):
            routes.initialize_route(route_metadata)
        existing_route = routes.get(route_metadata)

        # Update hit count :
        thread_hits = int(route["thread_hits"])
        existing_route["hits"] += thread_hits

        # Update API Spec :
        update_route_info(route["apispec"], existing_route)

    return {
        "routes": list(connection_manager.routes),
        "endpoints": connection_manager.conf.endpoints,
        "bypassed_ips": connection_manager.conf.bypassed_ips,
        "blocked_uids": connection_manager.conf.blocked_uids,
    }
