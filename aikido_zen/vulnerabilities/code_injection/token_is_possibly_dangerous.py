"""Exports token_is_possibly_dangerous"""

import token

SAFE_OPERATIONS = [
    # Mathematical operations :
    "+",
    "-",
    "*",
    "%",
    "**",
    "//",
    # Comparison :
    "==",
    "!=",
    "<=",
    ">=",
    "<",
    ">",
    # Binary mathematical operations :
    "&",
    "~",
    "^",
    "<<",
    ">>",
    # Regarded as safe language tokens :
    ",",
    "True",
    "False",
]


def token_is_possibly_dangerous(tok):
    """
    Returns boolean indicating if the token is possibly dangerous,
    only marks "OP" and "NAME" types as dangerous and excludes list of SAFE_OPERATIONS.
    """

    if not tok.type == token.OP and not tok.type == token.NAME:
        # The token is neither an "OP" nor a "NAME" token, assume safe
        return False

    if tok.string in SAFE_OPERATIONS:
        # Check if the token is a safe operation (e.g. +, -, /, ==, ...)
        return False
    # If it can result in injection and it's not a safe operation, return True.
    return True
