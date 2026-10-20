from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.create_custom_event import create_custom_event
from . import get_current_context
import aikido_zen.thread.thread_cache as thread_cache
from aikido_zen.background_process.ipc import IPCClient
from ..background_process.commands import put_event

MAX_EVENTS_PER_REQUEST = 25

logged_warning_track_called_without_context = False


def track(event_name):
    """
    External function for applications to track a custom event, e.g. a
    failed login or a signup. Only works inside an HTTP request.
    """
    try:
        if not isinstance(event_name, str) or len(event_name) == 0:
            logger.info("track(...) expects a non-empty string as event name.")
            return

        ipc = IPCClient.get()
        if not ipc:
            return

        context = get_current_context()
        if not context:
            log_warning_track_called_without_context()
            return

        cache = thread_cache.get_cache()
        if cache and cache.is_bypassed_ip(context.remote_address):
            return

        if context.tracked_events >= MAX_EVENTS_PER_REQUEST:
            log_warning_event_limit_reached(context)
            return
        context.tracked_events += 1

        event = create_custom_event(event_name, context)
        if not event:
            return

        ipc.send_message_async(put_event.generate(event))
    except Exception as e:
        logger.debug("Exception occurred in track: %s", e)


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


def log_warning_event_limit_reached(context):
    """Logs a warning, but only once per request, that track(...) went over the limit"""
    if context.tracked_events_limit_warning_logged:
        return

    logger.warning(
        "track(...) was called more than %s times during one request. "
        "Only the first %s events were tracked.",
        MAX_EVENTS_PER_REQUEST,
        MAX_EVENTS_PER_REQUEST,
    )
    context.tracked_events_limit_warning_logged = True
