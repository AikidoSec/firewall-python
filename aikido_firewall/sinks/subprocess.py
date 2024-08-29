"""
Sink module for `subprocess`
"""

import copy
import importhook
import aikido_firewall.vulnerabilities as vulns

SUBPROCESS_OPERATIONS = ["call", "run", "check_call", "Popen", "check_output"]


def generate_aikido_function(op, former_func):
    """
    Generates an aikido shell function given
    an operation and a former function
    """

    def aikido_new_func(*args, op=op, former_func=former_func, **kwargs):
        command = None
        if len(args) != 0 and isinstance(args[0], (list | tuple | dict)):
            command = " ".join(args[0])
        elif len(args) != 0 and isinstance(args[0], str):
            command = args[0]
        if command:
            vulns.run_vulnerability_scan(
                kind="shell_injection",
                op=f"subprocess.{op}",
                args=(command,),
            )
        return former_func(*args, **kwargs)

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
