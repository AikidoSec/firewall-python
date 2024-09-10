"""
Sink module for `subprocess`
"""

import copy
import aikido_zen.importhook as importhook
import aikido_zen.vulnerabilities as vulns

SUBPROCESS_OPERATIONS = ["call", "run", "check_call", "Popen", "check_output"]


def generate_aikido_function(op, former_func):
    """
    Generates an aikido shell function given
    an operation and a former function
    """

    def aikido_new_func(args, *arguments, op=op, former_func=former_func, **kwargs):
        shell_enabled = kwargs.get("shell")
        command = None
        if isinstance(args, str):
            command = args
        elif hasattr(args, "__iter__"):
            # Check if args is an iterable i.e. list, dict, tuple
            # If it is we join it with spaces to run the shell_injection algorithm.
            command = " ".join(args)

        # For all operations above: call, run, check_call, Popen, check_output, default value
        # of the shell property is False.
        if command and shell_enabled == True:
            vulns.run_vulnerability_scan(
                kind="shell_injection",
                op=f"subprocess.{op}",
                args=(command,),
            )
        return former_func(args, *arguments, **kwargs)

    return aikido_new_func


@importhook.on_import("subprocess")
def on_subprocess_import(subprocess):
    """
    Hook 'n wrap on `subproccess`, wrapping multiple functions
    Returns : Modified subprocess object
    """
    modified_subprocess = importhook.copy_module(subprocess)
    for op in SUBPROCESS_OPERATIONS:
        former_func = copy.deepcopy(getattr(subprocess, op))
        setattr(
            modified_subprocess,
            op,
            generate_aikido_function(op=op, former_func=former_func),
        )

    return modified_subprocess
