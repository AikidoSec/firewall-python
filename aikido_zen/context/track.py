"""
Track file, exports the track function
"""

from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.create_detected_attack_api_event import (
    extract_request_if_possible,
)
from . import get_current_context
import aikido_zen.background_process.comms as comms
from ..background_process.commands import PutEventCommand
from ..helpers.ipc.send_payload import send_payload

logged_warning_track_called_without_context = False


def track(event_name):
    """
    External function for applications to track a custom event, e.g. a
    failed login or a signup. Only works inside an HTTP request.
    """
    if not isinstance(event_name, str) or len(event_name) == 0:
        logger.info("track(...) expects a non-empty string as event name.")
        return

    context = get_current_context()
    if not context:
        log_warning_track_called_without_context()
        return

    event = {
        "type": "custom",
        "name": event_name,
        "request": extract_request_if_possible(context),
        "user": context.user,
    }

    ipc = comms.get_comms()
    if not ipc:
        return
    send_payload(ipc, PutEventCommand.generate(event))


def log_warning_track_called_without_context():
    """Logs a warning, but only once, that track(...) was called without a context"""
    global logged_warning_track_called_without_context  # pylint: disable=global-statement
    if logged_warning_track_called_without_context:
        return

    logger.warning(
        "track(...) was called without a context. The event will not be tracked. "
        "Make sure to call track(...) within an HTTP request."
    )
    logged_warning_track_called_without_context = True
