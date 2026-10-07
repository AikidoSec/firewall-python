from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_zen.helpers.logging import logger


def create_custom_event(event_name, context):
    try:
        event = {
            "type": "custom",
            "time": get_unixtime_ms(),
            "name": event_name,
            "request": extract_request_if_possible(context),
        }
        user = getattr(context, "user", None)
        if user:
            event["user"] = user
        return event
    except Exception as e:
        logger.error("Failed to create custom API event: %s", str(e))
        return None


def extract_request_if_possible(context):
    if not context:
        return None
    return {
        "method": getattr(context, "method", None),
        "ipAddress": getattr(context, "remote_address", None),
        "userAgent": context.get_user_agent(),
        "source": getattr(context, "source", None),
        "route": getattr(context, "route", None),
    }
