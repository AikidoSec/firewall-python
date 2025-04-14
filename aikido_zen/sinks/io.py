"""
Sink module for python's `io`
"""

from wrapt import when_imported
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import try_wrap_function_wrapper


def _open(func, instance, args, kwargs):
    file = get_argument(args, kwargs, 0, "file")
    if not file:
        return func(*args, **kwargs)

    vulns.run_vulnerability_scan(kind="path_traversal", op="io.open", args=(file,))

    return func(*args, **kwargs)


def _open_code(func, instance, args, kwargs):
    path = get_argument(args, kwargs, 0, "path")
    if not path:
        return func(*args, **kwargs)

    vulns.run_vulnerability_scan(kind="path_traversal", op="io.open_code", args=(path,))

    return func(*args, **kwargs)


@when_imported("io")
def patch(m):
    """
    patching module io
    - patches io.open(file, ...)
    - patches io.open_code(path)
    """
    try_wrap_function_wrapper(m, "open", _open)
    try_wrap_function_wrapper(m, "open_code", _open_code)
