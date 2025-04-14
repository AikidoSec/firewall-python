"""
Sink module for `builtins`, python's built-in function
"""

from pathlib import PurePath
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import patch_function, on_import, before


@before
def _open(func, instance, args, kwargs):
    filename = get_argument(args, kwargs, 0, "filename")
    if not isinstance(filename, (str, bytes, PurePath)):
        return

    vulns.run_vulnerability_scan(
        kind="path_traversal", op="builtins.open", args=(filename,)
    )


@on_import("builtins")
def patch(m):
    """
    patching module builtins
    - patches builtins.open
    """
    patch_function(m, "open", _open)
