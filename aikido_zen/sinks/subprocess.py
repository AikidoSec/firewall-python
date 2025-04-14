"""
Sink module for `subprocess`
"""

from wrapt import when_imported
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import try_wrap_function_wrapper


@when_imported("subprocess")
def patch(m):
    """
    patching subprocess module
    - patches Popen.__init__ constructor
    - does not patch: check_output, check_call, call, and run (call Popen class)
    """
    try_wrap_function_wrapper(m, "Popen.__init__", _subprocess_init)


def _subprocess_init(func, instance, args, kwargs):
    shell_arguments = get_argument(args, kwargs, 0, "args")
    shell_enabled = get_argument(args, kwargs, 8, "shell")
    if not shell_enabled:
        # default shell property is False, we only want to scan if it's True
        return func(*args, **kwargs)

    command = try_join_iterable(shell_arguments)
    if isinstance(shell_arguments, str):
        command = shell_arguments

    if command:
        vulns.run_vulnerability_scan(
            kind="shell_injection",
            op=f"subprocess.Popen",
            args=(command,),
        )

    return func(*args, **kwargs)


def try_join_iterable(iterable):
    try:
        return " ".join(iterable)
    except Exception:
        return None
