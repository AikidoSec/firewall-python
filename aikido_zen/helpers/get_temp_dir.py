"""
Helper function file, see function docstring
"""

import os


def get_temp_dir():
    """
    Checks the environment variable "AIKIDO_TMP_DIR"
    """
    aikido_temp_dir_env = os.getenv("AIKIDO_TMP_DIR")
    if aikido_temp_dir_env is not None:
        return aikido_temp_dir_env
    return "/tmp"
