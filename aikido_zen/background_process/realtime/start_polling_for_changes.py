"""
Mainly exports `start_polling_for_changes` function
"""

from aikido_zen.helpers.token import Token
from aikido_zen.helpers.logging import logger
import aikido_zen.background_process.realtime as realtime

POLL_FOR_CONFIG_CHANGES_INTERVAL = 60  #  Poll for config changes every 60 seconds


def start_polling_for_changes(connection_manager, event_scheduler):
    """
    Arguments :
    - on_config_update : A function that will run with the new config if changed
    - serverless, token : Attributes from the connection_manager
    - last_updated_at : The last time the config was updated (unixtime in ms)
    This function will check if the config was updated or not
    """
    if not isinstance(connection_manager.token, Token):
        logger.info("No token provided, not polling for config updates")
        return
    if connection_manager.serverless:
        logger.info("Running in serverless environment, not polling for config updates")
        return

    # Start the interval by booting the first settimeout
    poll_for_changes(
        connection_manager=connection_manager,
        token=connection_manager.token,
        former_last_updated=connection_manager.conf.last_updated_at,
        event_scheduler=event_scheduler,
    )


def poll_for_changes(
    connection_manager,
    token,
    former_last_updated,
    event_scheduler,
):
    """
    Actually performs the check if the config was updated or not
    """
    # If something went wrong, or we don't know when the config was
    # last updated, set to prev value
    last_updated = former_last_updated
    try:
        last_updated = realtime.get_config_last_updated_at(token)
        config_changed = (
            isinstance(former_last_updated, int) and last_updated > former_last_updated
        )
        if config_changed:
            #  The config changed
            logger.debug("According to realtime: Config changed")
            config = realtime.get_config(token)
            connection_manager.update_service_config({**config, "success": True})
            connection_manager.update_blocked_ip_addresses()
    except Exception as e:
        logger.error("Failed to check for config updates due to error : %s", e)

    # Set a timeout for `POLL_FOR_CONFIG_CHANGES_INTERVAL` seconds until this function
    # Gets called again
    event_scheduler.enter(
        POLL_FOR_CONFIG_CHANGES_INTERVAL,
        1,
        poll_for_changes,
        (connection_manager, token, last_updated, event_scheduler),
    )
