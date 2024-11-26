"""
Sink module for `os`, wrapping os.system
"""

import aikido_zen.importhook as importhook
import aikido_zen.vulnerabilities as vulns


@importhook.on_import("os")
def on_os_import(os):
    """
    Hook 'n wrap on `os.system()` function
    Returns : Modified os object
    We don't wrap os.popen() since this command uses subprocess.Popen, which we
    already wrap and protect in the subprocess.py sink.
    We also don't wrap os.execl, os.execle, os.execlp, ... because these should only be vulnerable
    to argument injection, which we currently don't protect against.
    """
    modified_os = importhook.copy_module(os)

    def aikido_new_system(command, *args, **kwargs):
        if isinstance(command, str):
            vulns.run_vulnerability_scan(
                kind="shell_injection", op="os.system", args=(command,)
            )
        return os.system(command, *args, **kwargs)

    setattr(modified_os, "system", aikido_new_system)
    return modified_os
