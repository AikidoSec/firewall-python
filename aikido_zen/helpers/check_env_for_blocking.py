"""
Helper function file, see function docstring
"""

import os


def check_env_for_blocking():
    """
    Checks the environment variable "AIKIDO_BLOCK"
    """
    # Set log level
    aikido_blocking_env = os.getenv("AIKIDO_BLOCK")
    if aikido_blocking_env is None:
        aikido_blocking_env = os.getenv(
            "AIKIDO_BLOCKING"
        )  # Fallback to AIKIDO_BLOCKING.
    if aikido_blocking_env is not None:
        return aikido_blocking_env.lower() in ["true", "1"]
    return False
