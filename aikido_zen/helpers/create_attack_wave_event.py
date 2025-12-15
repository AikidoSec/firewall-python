from aikido_zen.helpers.limit_length_metadata import limit_length_metadata
from aikido_zen.helpers.logging import logger


def create_attack_wave_event(context, metadata):
    try:
        return {
            "type": "detected_attack_wave",
            "attack": {
                "user": getattr(context, "user", None),
                "metadata": limit_length_metadata(metadata, 4096),
            },
            "request": extract_request_if_possible(context),
        }
    except Exception as e:
        logger.error("Failed to create detected_attack_wave API event: %s", str(e))
        return None


def extract_request_if_possible(context):
    if not context:
        return None
    return {
        "ipAddress": getattr(context, "remote_address", None),
        "source": getattr(context, "source", None),
        "userAgent": context.get_user_agent(),
    }
