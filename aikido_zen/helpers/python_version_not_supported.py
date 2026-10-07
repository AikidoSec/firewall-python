import sys
from aikido_zen.helpers.logging import logger


def python_version_not_supported() -> bool:
    major = sys.version_info.major
    minor = sys.version_info.minor
    if major != 3:
        logger.error("This version of Zen only supports Python 3")
        return True
    if minor > 14:
        logger.error("This version of Zen doesn't support versions above Python 3.14")
        return True
    return False
