"""
Sink module for python's `os`
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.vulnerabilities.path_traversal.check_context_for_path_traversal import (
    check_context_for_path_traversal,
)
from aikido_firewall.context import get_current_context
from aikido_firewall.background_process import get_comms
from aikido_firewall.errors import AikidoPathTraversal
from aikido_firewall.helpers.blocking_enabled import is_blocking_enabled

# File functions :
OS_FILE_FUNCTIONS = [
    "access",
    "chmod",
    "chown",
    "mkdir",
    "listdir",
    "readlink",
    "unlink",
    "rename",
    "rmdir",
    "remove",
    "symlink",
    "stat",
    "link",
    "makedirs",
    "walk",
]
OS_PATH_FUNCTIONS = [
    "exists",
    "realpath",
    "getsize",
    "getmtime",
    "getatime",
    "getctime",
]
# os.path.join(path, *paths) is not wrapped


def generate_aikido_function(op, former_func):
    """
    Returns a generated aikido function given an operation
    and the previous function
    """

    def aikido_new_func(*args, op=op, former_func=former_func, **kwargs):
        logger.debug("`os` wrapper, filepath : `%s`; OP : `%s`", args[0], op)
        context = get_current_context()
        if not context:
            return former_func(*args, **kwargs)
        result = check_context_for_path_traversal(
            filename=args[0], operation=f"os.{op}", context=context
        )
        if len(result) != 0:
            get_comms().send_data_to_bg_process("ATTACK", (result, context))
            if is_blocking_enabled():
                raise AikidoPathTraversal()
        return former_func(*args, **kwargs)

    return aikido_new_func


@importhook.on_import("os")
def on_os_import(os):
    """
    Hook 'n wrap on `os`, python's built-in functions
    Our goal is to wrap the open() function, which you use when opening files
    Returns : Modified os object
    """
    modified_os = importhook.copy_module(os)
    for op in OS_FILE_FUNCTIONS:
        # Wrap os. functions
        former_func = copy.deepcopy(getattr(os, op))
        aikido_new_func = generate_aikido_function(op, former_func)
        setattr(os, op, aikido_new_func)
        setattr(modified_os, op, aikido_new_func)

    for op in OS_PATH_FUNCTIONS:
        # Wrap os.path functions
        former_func = copy.deepcopy(getattr(os.path, op))
        aikido_new_func = generate_aikido_function(f"path.{op}", former_func)
        setattr(os.path, op, aikido_new_func)
        # pylint: disable=no-member
        setattr(modified_os.path, op, aikido_new_func)

    logger.debug("Wrapped `os` module")
    return modified_os
