"""
Sink module for python's `shutil`
"""

import copy
import aikido_zen.importhook as importhook
import aikido_zen.vulnerabilities as vulns

# File functions func(src, dst, *, **)
SHUTIL_SRC_DST_FUNCTIONS = [
    "copymode",
    "copystat",
    "copytree",
    "move",
]
# shutil.copyfile(src, dst, *, **) => builtins.open
# shutil.copy(src, dst, *, **) => builtins.open
# shutil.copy2(src, dst, *, **) => builtins.open


def generate_aikido_function(op, former_func):
    """
    Returns a generated aikido function given an operation
    and the previous function
    """

    def aikido_new_func(
        src, dst, *args, aik_op=op, aik_former_func=former_func, **kwargs
    ):
        kind = "path_traversal"
        op = f"shutil.{aik_op}"
        if src:
            vulns.run_vulnerability_scan(kind, op, args=(src,))
        if dst:
            vulns.run_vulnerability_scan(kind, op, args=(dst,))
        return former_func(src, dst, *args, **kwargs)

    return aikido_new_func


@importhook.on_import("shutil")
def on_shutil_import(shutil):
    """
    Hook 'n wrap on `shutil`, python's built-in functions
    Our goal is to wrap functions found in SHUTIL_SRC_DST_FUNCTIONS
    Returns : Modified shutil object
    """
    modified_shutil = importhook.copy_module(shutil)
    for op in SHUTIL_SRC_DST_FUNCTIONS:
        # Wrap shutil. functions
        former_func = copy.deepcopy(getattr(shutil, op))
        aikido_new_func = generate_aikido_function(op, former_func)
        setattr(shutil, op, aikido_new_func)
        setattr(modified_shutil, op, aikido_new_func)

    return modified_shutil
