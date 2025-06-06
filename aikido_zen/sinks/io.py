"""
Sink module for python's `io`
"""

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import patch_function, before, on_import


@before
def _open(func, instance, args, kwargs):
    file = get_argument(args, kwargs, 0, "file")
    if not file:
        return

    op = "io.open"
    register_call(op, "fs_op")

    vulns.run_vulnerability_scan(kind="path_traversal", op=op, args=(file,))


@before
def _open_code(func, instance, args, kwargs):
    path = get_argument(args, kwargs, 0, "path")
    if not path:
        return

    op = "io.open_code"
    register_call(op, "fs_op")

    vulns.run_vulnerability_scan(kind="path_traversal", op=op, args=(path,))


@on_import("io")
def patch(m):
    """
    patching module io
    - patches io.open(file, ...)
    - patches io.open_code(path)
    """
    patch_function(m, "open", _open)
    patch_function(m, "open_code", _open_code)
