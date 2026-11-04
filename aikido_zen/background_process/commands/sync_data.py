from aikido_zen.background_process.packages import PackagesStore
from aikido_zen.helpers.ipc.command_types import Payload

IDENTIFIER = "SYNC_DATA"


def generate(request, timeout_in_sec=5) -> Payload:
    return Payload(IDENTIFIER, request, timeout_in_sec)


def process(connection_manager, request, queue):
    """
    Application -> Background process: Routes, Hostnames, Users, Stats & middleware installed.
    Background process -> Application: Config, only when the revision has changed.
    """

    # Sync routes
    routes = connection_manager.routes
    for route in request.get("current_routes", {}).values():
        route_metadata = {"method": route["method"], "route": route["path"]}
        if not routes.get(route_metadata):
            routes.initialize_route(route_metadata)
        existing_route = routes.get(route_metadata)

        # Update hit count :
        hits_delta_since_sync = int(route.get("hits_delta_since_sync", 0))
        existing_route["hits"] += hits_delta_since_sync

        # Update API Spec :
        routes.update_route_with_apispec(route_metadata, route["apispec"])

    # Save middleware installed :
    if request.get("middleware_installed", False):
        connection_manager.middleware_installed = True

    # Sync hostnames
    for hostnames_entry in request.get("hostnames", []):
        connection_manager.hostnames.add(
            hostnames_entry["hostname"],
            hostnames_entry["port"],
            hostnames_entry["hits"],
        )

    # Sync users
    for user_entry in request.get("users", []):
        connection_manager.users.add_user_from_entry(user_entry)

    # Sync stats
    connection_manager.statistics.import_from_record(request.get("stats", {}))

    # Sync ai stats
    connection_manager.ai_stats.import_list(request.get("ai_stats", []))

    # Sync packages
    PackagesStore.import_list(request.get("packages", []))

    if (
        connection_manager.conf.last_updated_at > 0
        and request.get("config_revision") != connection_manager.conf.revision
    ):
        return {"config": connection_manager.conf}
    return {}
