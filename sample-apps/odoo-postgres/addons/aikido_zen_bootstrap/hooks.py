import logging

import aikido_zen

logger = logging.getLogger(__name__)


def post_load():
    aikido_zen.protect()
    logger.info("Aikido Zen bootstrap post_load completed")
