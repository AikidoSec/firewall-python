import sys

from aikido_zen.helpers.logging import logger


def gil_not_enabled() -> bool:
    is_gil_enabled = getattr(sys, "_is_gil_enabled", None)
    if is_gil_enabled is not None and not is_gil_enabled():
        logger.error("Zen does not support running Python with the GIL disabled")
        return True
    return False
