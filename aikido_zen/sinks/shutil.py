"""
Sink module for python's `shutil`
"""

from wrapt import when_imported

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import try_wrap_function_wrapper


def _shutil_func(func, instance, args, kwargs):
    source = get_argument(args, kwargs, 0, "src")
    destination = get_argument(args, kwargs, 1, "dst")

    kind = "path_traversal"
    op = f"shutil.{func.__name__}"
    if source:
        vulns.run_vulnerability_scan(kind, op, (source,))
    if destination:
        vulns.run_vulnerability_scan(kind, op, (destination,))

    return func(*args, **kwargs)


@when_imported("shutil")
def patch(m):
    """
    patching module shutil
    - patches: copymode, copystat, copytree, move
    - does not patch: copyfile, copy, copy2 -> uses builtins.open
    """
    try_wrap_function_wrapper(m, "copymode", _shutil_func)
    try_wrap_function_wrapper(m, "copystat", _shutil_func)
    try_wrap_function_wrapper(m, "copytree", _shutil_func)
    try_wrap_function_wrapper(m, "move", _shutil_func)
