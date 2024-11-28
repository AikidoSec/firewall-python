"""
Sink module for `builtins`, python's built-in function
"""

from pathlib import PurePath
import aikido_zen.importhook as importhook
import aikido_zen.vulnerabilities as vulns


def aikido_open_decorator(func):
    """Decorator for open(...)"""

    def wrapper(*args, **kwargs):
        #  args[0] is thefunc_name filename
        if len(args) > 0 and isinstance(args[0], (str, bytes, PurePath)):
            vulns.run_vulnerability_scan(
                kind="path_traversal", op="builtins.open", args=(args[0],)
            )
        return func(*args, **kwargs)

    return wrapper


@importhook.on_import("builtins")
def on_builtins_import(builtins):
    """
    Hook 'n wrap on `builtins`, python's built-in functions
    Our goal is to wrap the open() function, which you use when opening files
    Returns : Modified builtins object
    """
    modified_builtins = importhook.copy_module(builtins)

    # pylint: disable=no-member
    setattr(builtins, "open", aikido_open_decorator(builtins.open))
    setattr(modified_builtins, "open", aikido_open_decorator(builtins.open))
    return modified_builtins
