"""
Sink module for python's `pathlib`
"""

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import before, patch_function, on_import


@before
def _pathlib_truediv_patch(func, instance, args, kwargs):
    path = get_argument(args, kwargs, 0, "key")
    op = "pathlib.PurePath.__truediv__"
    register_call(op, "fs_op")

    vulns.run_vulnerability_scan(kind="path_traversal", op=op, args=(path,))


@on_import("pathlib")
def patch(m):
    """
    patching module pathlib
    - patches PurePath.__truediv__ : Path() / Path() -> join operation
    """

    # PurePath() / "my/path/test.txt"
    # This is accomplished by overloading the __truediv__ function on the Path class
    patch_function(m, "PurePath.__truediv__", _pathlib_truediv_patch)
