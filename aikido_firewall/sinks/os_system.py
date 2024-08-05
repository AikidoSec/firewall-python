"""
Sink module for `os`, wrapping os.system
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


@importhook.on_import("os")
def on_os_import(os):
    """
    Hook 'n wrap on `os.system()` function
    Returns : Modified os object
    """
    modified_os = importhook.copy_module(os)

    former_system_func = copy.deepcopy(os.system)

    def aikido_new_system(*args, former_system_func=former_system_func, **kwargs):
        logger.debug("Wrapper - `os`")

        context = get_current_context()
        if not context:
            former_system_func(*args, **kwargs)
        contains_injection = check_context_for_shell_injection(
            command=args[0], operation="os.system", context=context
        )

        logger.debug("Shell injection results : %s", json.dumps(contains_injection))
        if contains_injection:
            get_comms().send_data_to_bg_process("ATTACK", (contains_injection, context))
            should_block = get_comms().send_data_to_bg_process(
                action="READ_PROPERTY", obj="block", receive=True
            )
            if should_block:
                raise AikidoShellInjection()

        return former_system_func(*args, **kwargs)

    # pylint: disable=no-member
    setattr(os, "system", aikido_new_system)
    logger.debug("Wrapped `os` module")
    return modified_os
