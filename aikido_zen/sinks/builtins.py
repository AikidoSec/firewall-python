"""
Sink module for `builtins`, python's built-in function
"""

from pathlib import PurePath
import copy
import aikido_zen.importhook as importhook
import aikido_zen.vulnerabilities as vulns


@importhook.on_import("builtins")
def on_builtins_import(builtins):
    """
    Hook 'n wrap on `builtins`, python's built-in functions
    Our goal is to wrap the open() function, which you use when opening files
    Returns : Modified builtins object
    """
    modified_builtins = importhook.copy_module(builtins)

    former_open = copy.deepcopy(builtins.open)
    former_eval = copy.deepcopy(builtins.eval)
    former_exec = copy.deepcopy(builtins.exec)
    former_compile = copy.deepcopy(builtins.compile)

    # Path Traversal :
    def aikido_new_open(*args, **kwargs):
        #  args[0] is the filename
        if len(args) > 0 and isinstance(args[0], (str, bytes, PurePath)):
            vulns.run_vulnerability_scan(
                kind="path_traversal", op="builtins.open", args=(args[0],)
            )
        return former_open(*args, **kwargs)

    # Code injection :
    def aikido_new_eval(expression, *args, **kwargs):
        if expression and isinstance(expression, str):
            vulns.run_vulnerability_scan(
                kind="code_injection", op="builtins.eval", args=expression
            )
        return former_eval(expression, *args, **kwargs)

    def aikido_new_exec(object, *args, **kwargs):
        if object and isinstance(object, str):
            vulns.run_vulnerability_scan(
                kind="code_injection", op="builtins.exec", args=object
            )
        return former_exec(object, *args, **kwargs)

    def aikido_new_compile(source, *args, **kwargs):
        code = source
        if isinstance(source, bytes):
            code = source.decode("utf-8")
        if code and isinstance(code, str):
            vulns.run_vulnerability_scan(
                kind="code_injection", op="builtins.compile", args=code
            )
        return former_compile(source, *args, **kwargs)

    # pylint: disable=no-member
    setattr(builtins, "open", aikido_new_open)
    setattr(modified_builtins, "open", aikido_new_open)
    setattr(builtins, "eval", aikido_new_eval)
    setattr(modified_builtins, "eval", aikido_new_eval)
    setattr(builtins, "exec", aikido_new_exec)
    setattr(modified_builtins, "exec", aikido_new_exec)
    setattr(builtins, "compile", aikido_new_compile)
    setattr(modified_builtins, "compile", aikido_new_compile)
    return modified_builtins
