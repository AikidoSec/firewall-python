"""
Sink module for python's `os`
"""

import copy
from pathlib import PurePath
import aikido_zen.importhook as importhook
import aikido_zen.vulnerabilities as vulns

# os.func(...) functions, can have a filename and destination.
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
    "walk",
    "open",
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
