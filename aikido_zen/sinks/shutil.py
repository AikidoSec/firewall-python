"""
Sink module for python's `shutil`
"""

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, patch_function, before


@before
def _shutil_func(func, instance, args, kwargs):
    source = get_argument(args, kwargs, 0, "src")
    destination = get_argument(args, kwargs, 1, "dst")

    kind = "path_traversal"
    op = f"shutil.{func.__name__}"
    if isinstance(source, str):
        vulns.run_vulnerability_scan(kind, op, args=(source,))
    if isinstance(source, str):
        vulns.run_vulnerability_scan(kind, op, args=(destination,))


@on_import("shutil")
def patch(m):
    """
    patching module shutil
    - patches: copymode, copystat, copytree, move
    - does not patch: copyfile, copy, copy2 -> uses builtins.open
    """
    patch_function(m, "copymode", _shutil_func)
    patch_function(m, "copystat", _shutil_func)
    patch_function(m, "copytree", _shutil_func)
    patch_function(m, "move", _shutil_func)
