"""
Sink module for `builtins`, python's built-in function
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.vulnerabilities.path_traversal.check_context_for_path_traversal import (
    check_context_for_path_traversal,
)
from aikido_firewall.context import get_current_context
from aikido_firewall.errors import AikidoPathTraversal


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
        result = check_context_for_path_traversal(
            filename=args[0], operation="builtins.open", context=get_current_context()
        )
        if len(result) != 0:
            raise AikidoPathTraversal()
        logger.info("File name openend : %s, in mode : `%s`", args[0], args[1])
        return former_open(*args, **kwargs)

    # pylint: disable=no-member
    setattr(builtins, "open", aikido_new_open)
    logger.debug("Wrapped `builtins` module")
    return modified_builtins
