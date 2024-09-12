"""Helper function file, see function docstring"""

import os

ENV_PREFIX = "AIKIDO_FEATURE_"


def is_feature_enabled(feature):
    """Checks if `feature` is enabled by checking ENV variables"""
    env_variable_name = ENV_PREFIX + feature.upper()
    env_value = os.getenv(env_variable_name)
    if env_value is not None:
        return env_value.lower() in ["true", "1"]
    return False
