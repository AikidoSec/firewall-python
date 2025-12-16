import json
from aikido_zen.helpers.limit_length_metadata import limit_length_metadata
from aikido_zen.helpers.logging import logger
from aikido_zen.storage.attack_wave_detector_store import attack_wave_detector_store


def create_attack_wave_event(context):
    try:
        metadata = {}

        samples = attack_wave_detector_store.get_samples_for_ip(context.remote_address)
        if samples:
            # Convert samples to JSON string, since metadata is a key-value store of strings.
            metadata["samples"] = json.dumps(samples)

        attack_wave_detector_store.clear_samples_for_ip(context.remote_address)

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
