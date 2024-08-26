"""Lambda init.py file"""

import aikido_firewall
from aikido_firewall.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from aikido_firewall.background_process.api.http_api import ReportingApiHTTP
from aikido_firewall.helpers.check_env_for_blocking import check_env_for_blocking
from aikido_firewall.helpers.token import get_token_from_env
from aikido_firewall.background_process.cloud_connection_manager.globals import (
    set_global_cloud_connection_manager,
)


def protect(handler):
    """Aikido protect function for the lambda"""
    # Set aikido global CloudConnectionManager
    api = ReportingApiHTTP("https://guard.aikido.dev/")
    cloud_connection_manager = CloudConnectionManager(
        block=check_env_for_blocking(),
        api=api,
        token=get_token_from_env(),
        serverless="lambda",
    )
    cloud_connection_manager.timeout_in_sec = 1 # 1 second timeout
    cloud_connection_manager.on_start()
    set_global_cloud_connection_manager(cloud_connection_manager)

    # Wrapping :
    aikido_firewall.protect("daemon_disabled")
    return handler
