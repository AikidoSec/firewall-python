import os
import platform
import sys

from aikido_zen.background_process import get_uds_filename
from aikido_zen.helpers.logging import logger


def test_uds_file_access():
    """Returns true if access is possible, false if it's not."""
    filename = get_uds_filename()
    directory = "/".join(filename.split("/")[:-1])

    if platform.system() == "Windows":
        # Python does not support Windows UDS just yet, so we have to rely on INET
        return True

    if not os.access(directory, os.R_OK) or not os.access(directory, os.W_OK):
        # We need both read and write permissions in order to start the socket
        logger.critical(
            "Cannot start Zen: no read/write permissions for directory %s. "
            + "You can change the path by setting "
            + "the AIKIDO_TMP_DIR environment variable.",
            directory,
        )
        return False
    return True
