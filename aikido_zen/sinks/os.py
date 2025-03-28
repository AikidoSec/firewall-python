"""
Sink module for python's `os`
"""

import copy
import platform
from pathlib import PurePath
import aikido_zen.importhook as importhook
import aikido_zen.vulnerabilities as vulns

# Common functions available on both Windows and Unix
COMMON_FILE_FUNCTIONS = [
    "access",
    "chmod",
    "mkdir",
    "listdir",
    "unlink",
    "rename",
    "rmdir",
    "remove",
    "walk",
    "open",
]

# Unix-specific functions
UNIX_FILE_FUNCTIONS = [
    "chown",
    "readlink",
    "symlink",
    "link",
]

# os.path.realpath, os.path.abspath aren't wrapped, since they use os.path.join
OS_PATH_FUNCTIONS = ["getsize", "join", "expanduser", "expandvars"]

# os.makedirs() is not wrapped since it uses os.mkdir() which we wrap
# os.path.exists() and functions alike are not wrapped for performance reasons.
# We also don't wrap the stat library : https://docs.python.org/3/library/stat.html


def generate_aikido_function(op, former_func):
    """
    Returns a generated aikido function given an operation
    and the previous function
    """

    def aikido_new_func(*args, op=op, former_func=former_func, **kwargs):
        for arg in args:
            if isinstance(arg, (str, bytes, PurePath)):
                vulns.run_vulnerability_scan(
                    kind="path_traversal", op=f"os.{op}", args=(arg,)
                )
        return former_func(*args, **kwargs)

    return aikido_new_func


@importhook.on_import("os")
def on_os_import(os):
    """
    Hook 'n wrap on `os` module, wrapping os.func(...) and os.path.func(...)
    Returns : Modified os object
    """
    modified_os = importhook.copy_module(os)
    
    # Select functions based on platform
    functions_to_wrap = COMMON_FILE_FUNCTIONS
    if platform.system() != "Windows":
        functions_to_wrap.extend(UNIX_FILE_FUNCTIONS)
    
    for op in functions_to_wrap:
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
