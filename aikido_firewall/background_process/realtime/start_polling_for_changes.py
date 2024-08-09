"""
Mainly exports `start_polling_for_changes` function
"""

from aikido_firewall.helpers.token import Token
from aikido_firewall.helpers.logging import logger
import aikido_firewall.background_process.realtime as realtime

POLL_FOR_CONFIG_CHANGES_INTERVAL = 60  #  Poll for config changes every 60 seconds


def start_polling_for_changes(on_config_update, serverless, token, event_scheduler):
    """
    Arguments :
    - on_config_update : A function that will run with the new config if changed
    - serverless, token : Attributes from the reporter
    - last_updated_at : The last time the config was updated (unixtime in ms)
    This function will check if the config was updated or not
    """
    if not isinstance(token, Token):
        logger.info("No token provided, not polling for config updates")
        return
    if serverless:
        logger.info("Running in serverless environment, not polling for config updates")
        return

    # Start the interval by booting the first settimeout
    poll_for_changes(on_config_update, token, 0, event_scheduler)


def poll_for_changes(on_config_update, token, former_last_updated, event_scheduler):
    """
    Actually performs the check if the config was updated or not
    """
    # If something went wrong, or we don't know when the config was
    # last updated, set to prev value
    config_last_updated_at = former_last_updated
    try:
        config_last_updated_at = realtime.get_config_last_updated_at(token)
        if (
            isinstance(former_last_updated, int)
            and config_last_updated_at > former_last_updated
        ):
            #  The config changed
            config = realtime.get_config(token)
            on_config_update({**config, "success": True})
    except Exception as e:
        logger.error("Failed to check for config updates due to error : %s", e)

    # Set a timeout for `POLL_FOR_CONFIG_CHANGES_INTERVAL` seconds until this function
    # Gets called again
    event_scheduler.enter(
        POLL_FOR_CONFIG_CHANGES_INTERVAL,
        1,
        poll_for_changes,
        (on_config_update, token, config_last_updated_at, event_scheduler),
    )
