"""
Sink module for `os`, wrapping os.system
"""

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import patch_function, before, on_import


@before
def _system(func, instance, args, kwargs):
    command = get_argument(args, kwargs, 0, "command")
    if not isinstance(command, str):
        return

    vulns.run_vulnerability_scan(
        kind="shell_injection", op="os.system", args=(command,)
    )


@on_import("os")
def patch(m):
    """
    patching os module
    - patches os.system for shell injection
    - does not patch: os.popen -> uses subprocess.Popen
    - does not patch: os.execl, os.execle, os.execlp, ... -> only argument injection
    """
    patch_function(m, "system", _system)
