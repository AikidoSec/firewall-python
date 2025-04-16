"""
Sink module for python's `os`
"""

from pathlib import PurePath
import aikido_zen.vulnerabilities as vulns
from aikido_zen.errors import AikidoException
from aikido_zen.importhook import on_import
from aikido_zen.sinks import before, patch_function


@before
def _os_patch(func, instance, args, kwargs):
    possible_paths = args + tuple(kwargs.values())
    for path in possible_paths:
        if not isinstance(path, (str, bytes, PurePath)):
            continue
        # change op if it's an os.path function
        op = f"os.{func.__name__}"
        if func.__name__ in ("getsize", "join", "expanduser", "expandvars", "realpath"):
            op = f"os.path.{func.__name__}"

        vulns.run_vulnerability_scan(kind="path_traversal", op=op, args=(path,))


@on_import("os")
def patch(m):
    """
    patching module os
    - patches os.* functions that take in paths
    - patches os.path.* functions that take in paths
    - doesn't patch os.makedirs -> uses os.mkdir
    - doesn't patch os.path.realpath or os.path.abspath -> uses os.path.join
    - doesn't patch os.path.exists and others -> to big of a performance impact
    - doesn't patch stat library https://docs.python.org/3/library/stat.html
    """
    # os.*(...) patches
    patch_function(m, "access", _os_patch)
    patch_function(m, "chmod", _os_patch)
    patch_function(m, "chown", _os_patch)
    patch_function(m, "mkdir", _os_patch)
    patch_function(m, "listdir", _os_patch)
    patch_function(m, "readlink", _os_patch)
    patch_function(m, "unlink", _os_patch)
    patch_function(m, "rename", _os_patch)
    patch_function(m, "rmdir", _os_patch)
    patch_function(m, "remove", _os_patch)
    patch_function(m, "symlink", _os_patch)
    patch_function(m, "link", _os_patch)
    patch_function(m, "walk", _os_patch)
    patch_function(m, "open", _os_patch)

    # os.path.*(...) patches
    patch_function(m, "path.getsize", _os_patch)
    patch_function(m, "path.join", _os_patch)
    patch_function(m, "path.expanduser", _os_patch)
    patch_function(m, "path.expandvars", _os_patch)
    patch_function(m, "path.realpath", _os_patch)  # Python 3.13
