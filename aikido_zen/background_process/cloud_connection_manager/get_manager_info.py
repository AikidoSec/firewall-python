"""Exports get_manager_info function"""

import socket
import platform
import aikido_zen.config as config
import aikido_zen.helpers.get_machine_ip as h


def get_manager_info(connection_manager):
    """
    This returns info about the connection_manager
    """
    return {
        "dryMode": not connection_manager.block,
        "hostname": socket.gethostname(),
        "version": config.PKG_VERSION,
        "library": "firewall-python",
        "ipAddress": h.get_ip(),
        "packages": {
            pkg: details["version"]
            for pkg, details in connection_manager.packages.items()
            if "version" in details and "supported" in details and details["supported"]
        },
        "serverless": bool(connection_manager.serverless),
        "stack": list(connection_manager.packages.keys())
        + ([connection_manager.serverless] if connection_manager.serverless else []),
        "os": {"name": platform.system(), "version": platform.release()},
        "preventedPrototypePollution": False,  # Get this out of the API maybe?
        "nodeEnv": "",
        "platform": {
            "name": platform.python_implementation(),
            "version": platform.python_version(),
        },
    }
