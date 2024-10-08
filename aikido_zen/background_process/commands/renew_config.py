"""Exports process_renew_config"""


def process_renew_config(connection_manager, data, conn, queue=None):
    """Fetches all config data needed for thread-local cache"""

    # Process data here.

    return {
        "routes": list(connection_manager.routes),
        "endpoints": connection_manager.conf.endpoints,
        "bypassed_ips": connection_manager.conf.bypassed_ips,
        "blocked_uids": connection_manager.conf.blocked_uids,
    }
