"""exports `process_kill`"""

import sys
from aikido_zen.helpers.logging import logger


def process_kill(connection_manager, data, queue=None):
    """when main process quits , or during testing etc"""
    logger.info("Killing background process")
    sys.exit(0)
