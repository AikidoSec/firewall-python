"""
Sink module for python's `os`
"""

import copy
import importhook
from aikido_firewall.vulnerabilities import run_vulnerability_scan

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
    "link",
    "makedirs",
    "walk",
]
OS_PATH_FUNCTIONS = [
    "realpath",
    "getsize",
]
# os.path.join(path, *paths) is not wrapped


def generate_aikido_function(op, former_func):
    """
    Returns a generated aikido function given an operation
    and the previous function
    """

    def aikido_new_func(*args, op=op, former_func=former_func, **kwargs):
        #  args[0] : filename
        run_vulnerability_scan(kind="path_traversal", op=f"os.{op}", args=(args[0],))
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

    return modified_os
