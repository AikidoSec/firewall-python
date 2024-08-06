"""
Sink module for `subprocess`
"""

import copy
import json
import importhook
from aikido_firewall.context import get_current_context
from aikido_firewall.vulnerabilities.shell_injection.check_context_for_shell_injection import (
    check_context_for_shell_injection,
)
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process import get_comms
from aikido_firewall.errors import AikidoShellInjection

SUBPROCESS_OPERATIONS = ["call", "run", "check_call", "Popen", "check_output"]


def generate_aikido_function(op, former_func):
    """
    Generates an aikido shell function given
    an operation and a former function
    """

    def aikido_new_func(*args, op=op, former_func=former_func, **kwargs):
        logger.debug("Wrapper - `subprocess` on %s() function", op)
        if isinstance(args[0], list):
            command = " ".join(args[0])
        else:
            command = args[0]

        context = get_current_context()
        if not context:
            return former_func(*args, **kwargs)
        contains_injection = check_context_for_shell_injection(
            command=command, operation=f"subprocess.{op}", context=context
        )

        logger.debug("Shell injection results : %s", json.dumps(contains_injection))
        if contains_injection:
            get_comms().send_data_to_bg_process("ATTACK", (contains_injection, context))
            should_block_res = get_comms().send_data_to_bg_process(
                action="READ_PROPERTY", obj="block", receive=True
            )
            if should_block_res["success"] and should_block_res["data"]:
                raise AikidoShellInjection()

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

    logger.debug("Wrapped `subprocess` module")
    return modified_subprocess
