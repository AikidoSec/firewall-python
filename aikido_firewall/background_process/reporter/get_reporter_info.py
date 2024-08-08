"""Exports get_reporter_info function"""

import socket
import platform
from aikido_firewall.config import PKG_VERSION
from aikido_firewall.helpers.get_machine_ip import get_ip


def get_reporter_info(reporter):
    """
    This returns info about the reporter
    """
    return {
        "dryMode": not reporter.block,
        "hostname": socket.gethostname(),
        "version": PKG_VERSION,
        "library": "firewall-python",
        "ipAddress": get_ip(),
        "packages": {
            pkg: details["version"]
            for pkg, details in reporter.packages.items()
            if "version" in details and "supported" in details and details["supported"]
        },
        "serverless": bool(reporter.serverless),
        "stack": list(reporter.packages.keys())
        + ([reporter.serverless] if reporter.serverless else []),
        "os": {"name": platform.system(), "version": platform.release()},
        "preventedPrototypePollution": False,  # Get this out of the API maybe?
        "nodeEnv": "",
    }
