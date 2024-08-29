"""
Sink module for `os`, wrapping os.system
"""

import copy
import importhook
import aikido_firewall.vulnerabilities as vulns


@importhook.on_import("os")
def on_os_import(os):
    """
    Hook 'n wrap on `os.system()` function
    Returns : Modified os object
    """
    modified_os = importhook.copy_module(os)

    former_system_func = copy.deepcopy(os.system)

    def aikido_new_system(
        command, *args, former_system_func=former_system_func, **kwargs
    ):
        if isinstance(command, str):
            vulns.run_vulnerability_scan(
                kind="shell_injection", op="os.system", args=(command,)
            )
        return former_system_func(command, *args, **kwargs)

    setattr(os, "system", aikido_new_system)
    setattr(modified_os, "system", aikido_new_system)

    return modified_os
