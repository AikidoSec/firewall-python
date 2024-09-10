"""
Sink module for python's `io`
"""

import copy
import aikido_zen.importhook as importhook
import aikido_zen.vulnerabilities as vulns

KIND = "path_traversal"


@importhook.on_import("io")
def on_io_import(io):
    """
    Hook 'n wrap on `io`, wrapping io.open(...) and io.open_code(...)
    Returns : Modified io object
    """
    modified_io = importhook.copy_module(io)
    former_open_func = copy.deepcopy(io.open)
    former_open_code_func = copy.deepcopy(io.open_code)

    def aikido_open_func(file, *args, **kwargs):
        if file:
            vulns.run_vulnerability_scan(kind=KIND, op="io.open", args=(file,))
        return former_open_func(file, *args, **kwargs)

    def aikido_open_code_func(path):
        if path:
            vulns.run_vulnerability_scan(kind=KIND, op="io.open_code", args=(path,))
        return former_open_code_func(path)

    setattr(modified_io, "open", aikido_open_func)
    setattr(modified_io, "open_code", aikido_open_code_func)

    return modified_io
