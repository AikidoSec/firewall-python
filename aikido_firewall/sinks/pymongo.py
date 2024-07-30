
"""
Sink module for `pymongo`
"""
from importlib.metadata import version
import importhook
from aikido_firewall.helpers.logging import logger

@importhook.on_import("pymongo")
def on_pymongo_import(pymongo):
    """
    Hook 'n wrap on `pymongo`
    Our goal is to ...
    https://github.com/...
    Returns : Modified pymongo object
    """
    modified_pymongo = importhook.copy_module(pymongo)
    logger.debug("Wrapper - `pymongo` version : %s", version("pymongo"))

    return modified_pymongo
