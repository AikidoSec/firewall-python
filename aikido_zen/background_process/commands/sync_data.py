"""Exports process_renew_config"""

from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.helpers.logging import logger


def process_sync_data(connection_manager, data, conn, queue=None):
    """
    Synchronizes data between the thread-local cache (with a TTL of usually 1 minute) and the
    background thread. Which data gets synced?
    Thread -> BG Process : Hits, request statistics, api specs, hostnames
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

    # Save request data :
    connection_manager.statistics.requests["total"] += data.get("reqs", 0)

    # Save middleware installed :
    if data.get("middleware_installed", False):
        connection_manager.middleware_installed = True

    # Sync hostnames
    for hostnames_entry in data.get("hostnames", list()):
        connection_manager.hostnames.add(
            hostnames_entry["hostname"],
            hostnames_entry["port"],
            hostnames_entry["hits"],
        )

    # Sync users
    for user_entry in data.get("users", list()):
        connection_manager.users.add_user_from_entry(user_entry)

    if connection_manager.conf.last_updated_at > 0:
        # Only report data if the config has been fetched.
        return {
            "routes": dict(connection_manager.routes.routes),
            "config": connection_manager.conf,
        }
    return {}
