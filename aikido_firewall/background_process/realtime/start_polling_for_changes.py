"""
Mainly exports `start_polling_for_changes` function
"""

from aikido_firewall.helpers.token import Token
from aikido_firewall.helpers.logging import logger
from . import get_config, get_config_last_updated_at

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
    # Start the interval :
    event_scheduler.enter(
        0,
        1,
        poll_for_changes,
        (on_config_update, token, 0, event_scheduler),
    )


def poll_for_changes(on_config_update, token, former_last_updated, event_scheduler):
    """
    Actually performs the check if the config was updated or not
    """
    try:
        config_last_updated_at = get_config_last_updated_at(token)
        if (
            isinstance(former_last_updated, int)
            and config_last_updated_at > former_last_updated
        ):
            #  The config changed
            config = get_config(token)
            on_config_update({**config, "success": True})
        else:
            # If something went wrong, or we don't know when the config was
            # last updated, set to prev value
            config_last_updated_at = former_last_updated
    except Exception as e:
        logger.debug("Failed to check for config updates due to error : %s", e)

    # Add poll_for_changes back onto the interval
    event_scheduler.enter(
        POLL_FOR_CONFIG_CHANGES_INTERVAL,
        1,
        poll_for_changes,
        (on_config_update, token, config_last_updated_at, event_scheduler),
    )
