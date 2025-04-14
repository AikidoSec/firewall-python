"""
Sink module for `builtins`, python's built-in function
"""

from pathlib import PurePath
from wrapt import when_imported
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import wrap_function_before


def _open(func, instance, args, kwargs):
    filename = get_argument(args, kwargs, 0, "filename")
    if filename is None or not isinstance(filename, (str, bytes, PurePath)):
        return func(*args, **kwargs)

    vulns.run_vulnerability_scan(
        kind="path_traversal", op="builtins.open", args=(filename,)
    )

    return func(*args, **kwargs)


@when_imported("builtins")
def patch(m):
    """
    patching module builtins
    - patches builtins.open
    """
    wrap_function_before(m, "open", _open)
