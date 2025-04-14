"""
Sink module for `subprocess`
"""

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, patch_function, before


def try_join_iterable(iterable):
    try:
        return " ".join(iterable)
    except Exception:
        return None


@before
def _subprocess_init(func, instance, args, kwargs):
    shell_arguments = get_argument(args, kwargs, 0, "args")
    shell_enabled = get_argument(args, kwargs, 8, "shell")
    if not shell_enabled:
        return  # default shell property is False, we only want to scan if it's True

    command = try_join_iterable(shell_arguments)
    if isinstance(shell_arguments, str):
        command = shell_arguments
    if not command:
        return
    vulns.run_vulnerability_scan(
        kind="shell_injection",
        op=f"subprocess.Popen",
        args=(command,),
    )


@on_import("subprocess")
def patch(m):
    """
    patching subprocess module
    - patches Popen.__init__ constructor
    - does not patch: check_output, check_call, call, and run (call Popen class)
    """
    patch_function(m, "Popen.__init__", _subprocess_init)
