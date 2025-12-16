from aikido_zen.helpers.limit_length_metadata import limit_length_metadata
from aikido_zen.helpers.logging import logger


def create_attack_wave_event(context, metadata, samples=None):
    try:
        # Prepare metadata with samples if provided
        event_metadata = metadata.copy() if metadata else {}

        if samples:
            # Convert samples to a more compact format for metadata
            samples_metadata = []
            for sample in samples:
                sample_meta = {
                    "method": sample.get("method"),
                    "route": sample.get("route"),
                    "ua": sample.get("user_agent"),  # Shortened key
                    "ts": sample.get("timestamp"),
                }
                samples_metadata.append(sample_meta)

            # Add samples to metadata
            event_metadata["samples"] = samples_metadata

        return {
            "type": "detected_attack_wave",
            "attack": {
                "user": getattr(context, "user", None),
                "metadata": limit_length_metadata(event_metadata, 4096),
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
