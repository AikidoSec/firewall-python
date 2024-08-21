"""
Mainly exports `start_polling_for_changes` function
"""

from aikido_firewall.helpers.token import Token
from aikido_firewall.helpers.logging import logger
import aikido_firewall.background_process.realtime as realtime

POLL_FOR_CONFIG_CHANGES_INTERVAL = 60  #  Poll for config changes every 60 seconds


def start_polling_for_changes(reporter, event_scheduler):
    """
    Arguments :
    - on_config_update : A function that will run with the new config if changed
    - serverless, token : Attributes from the reporter
    - last_updated_at : The last time the config was updated (unixtime in ms)
    This function will check if the config was updated or not
    """
    if not isinstance(reporter.token, Token):
        logger.info("No token provided, not polling for config updates")
        return
    if reporter.serverless:
        logger.info("Running in serverless environment, not polling for config updates")
        return

    # Start the interval by booting the first settimeout
    poll_for_changes(
        on_config_update=reporter.update_service_config,
        token=reporter.token,
        former_last_updated=reporter.conf.last_updated_at,
        event_scheduler=event_scheduler,
    )


def poll_for_changes(on_config_update, token, former_last_updated, event_scheduler):
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
            on_config_update({**config, "success": True})
    except Exception as e:
        logger.error("Failed to check for config updates due to error : %s", e)

    # Set a timeout for `POLL_FOR_CONFIG_CHANGES_INTERVAL` seconds until this function
    # Gets called again
    event_scheduler.enter(
        POLL_FOR_CONFIG_CHANGES_INTERVAL,
        1,
        poll_for_changes,
        (on_config_update, token, last_updated, event_scheduler),
    )
