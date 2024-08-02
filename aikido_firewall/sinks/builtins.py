"""
Sink module for `builtins`, python's built-in function
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger


@importhook.on_import("builtins")
def on_builtins_import(builtins):
    """
    Hook 'n wrap on `builtins`, python's built-in functions
    Our goal is to wrap the open() function, which you use when opening files
    Returns : Modified builtins object
    """
    modified_builtins = importhook.copy_module(builtins)

    former_open = copy.deepcopy(builtins.open)

    def aikido_new_open(*args, **kwargs):
        logger.info("File name openend : %s, in mode : `%s`", args[0], args[1])
        return former_open(*args, **kwargs)

    # pylint: disable=no-member
    setattr(builtins, "open", aikido_new_open)
    logger.debug("Wrapped `builtins` module")
    return modified_builtins
