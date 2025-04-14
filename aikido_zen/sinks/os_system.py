"""
Sink module for `os`, wrapping os.system
"""

from wrapt import when_imported

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import try_wrap_function_wrapper


def _system(func, instance, args, kwargs):
    command = get_argument(args, kwargs, 0, "command")
    if not isinstance(command, str):
        return func(*args, **kwargs)

    vulns.run_vulnerability_scan(
        kind="shell_injection", op="os.system", args=(command,)
    )

    return func(*args, **kwargs)


@when_imported("os")
def patch(m):
    """
    patching os module
    - patches os.system for shell injection
    - does not patch: os.popen -> uses subprocess.Popen
    - does not patch: os.execl, os.execle, os.execlp, ... -> only argument injection
    """
    try_wrap_function_wrapper(m, "system", _system)
