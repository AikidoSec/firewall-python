"""
Helper function file, see function docstring
"""

import os


def aikido_disabled_flag_active():
    """
    Checks the environment variable "AIKIDO_DISABLED"
    """
    aikido_disabled_env = os.getenv("AIKIDO_DISABLED")
    if aikido_disabled_env is not None:
        return aikido_disabled_env.lower() in ["true", "1"]
    return False
