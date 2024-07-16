"""
Logging helper, this will create and set logging
"""

import logging
import sys
import os


APPLICATION_NAME = "aikido_firewall"

# Set log level
aikido_debug_env = os.getenv("AIKIDO_DEBUG")
LOG_LEVEL = logging.INFO
if aikido_debug_env is not None:
    if aikido_debug_env.lower() in ["true", "false", "1", "0"]:
        debug = aikido_debug_env.lower() in ["true", "1"]
        LOG_LEVEL = logging.DEBUG if debug else logging.INFO

# Create a logger
logger = logging.getLogger(APPLICATION_NAME)

# Configure format
fmt = logging.Formatter("%(name)s: %(asctime)s | %(levelname)s |> %(message)s")
# Get stdout handler
stdout = logging.StreamHandler(stream=sys.stdout)
stdout.setLevel(LOG_LEVEL)
stdout.setFormatter(fmt)
logger.addHandler(stdout)

# Configure logger
logger.setLevel(LOG_LEVEL)
logger.debug("Created logger")
