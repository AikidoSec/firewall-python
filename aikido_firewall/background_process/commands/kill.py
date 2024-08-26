"""exports `process_kill`"""

import sys
from aikido_firewall.helpers.logging import logger


def process_kill(reporter, data, conn):
    """when main process quits , or during testing etc"""
    logger.info("Killing background process")
    conn.close()
    sys.exit(0)
