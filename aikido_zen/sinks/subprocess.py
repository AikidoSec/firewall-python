"""
Sink module for `subprocess`
"""

import copy
import aikido_zen.importhook as importhook
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument

SUBPROCESS_OPERATIONS = ["check_output"]
# check_call, call, and run all call Popen class


def generate_aikido_function(op, former_func):
    """
    Generates an aikido shell function given
    an operation and a former function
    """

    def aikido_new_func(*args, op=op, former_func=former_func, **kwargs):
        shell_enabled = kwargs.get("shell")

        position = (
            1 if op == "Popen" else 0
        )  # If it's a constructor, first argument is self
        shell_arguments = get_argument(args, kwargs, pos=position, name="args")

        command = None
        if isinstance(shell_arguments, str):
            command = shell_arguments
        elif hasattr(shell_arguments, "__iter__"):
            # Check if args is an iterable i.e. list, dict, tuple
            # If it is we join it with spaces to run the shell_injection algorithm.
            command = " ".join(shell_arguments)

        # For all operations above: call, run, check_call, Popen, check_output, default value
        # of the shell property is False.
        if command and shell_enabled:
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

    # Wrap Class Popen seperately:
    former_popen_constructor = copy.deepcopy(subprocess.Popen.__init__)
    setattr(
        getattr(modified_subprocess, "Popen"),
        "__init__",  # Popen is a class, modify it's constructor
        generate_aikido_function(op="Popen", former_func=former_popen_constructor),
    )

    return modified_subprocess
