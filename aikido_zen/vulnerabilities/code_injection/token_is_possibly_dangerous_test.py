import token
import pytest
from .token_is_possibly_dangerous import token_is_possibly_dangerous, SAFE_OPERATIONS


class Token:
    def __init__(self, type, string):
        self.type = type
        self.string = string


def test_token_is_possibly_dangerous_safe_operation():
    # Test that safe operations are not marked as dangerous
    for op in SAFE_OPERATIONS:
        assert not token_is_possibly_dangerous(Token(type=token.OP, string=op))


def test_token_is_possibly_dangerous_unsafe_operation():
    # Test that unsafe operations are marked as dangerous
    unsafe_ops = [
        "assign",
        "lshift",
        "rshift",
        "or",
        "and",
        "mod",
        "div",
        "pow",
        "uadd",
        "usub",
        "neg",
        "not_",
        "invert",
    ]
    for op in unsafe_ops:
        assert token_is_possibly_dangerous(Token(type=token.OP, string=op))


def test_token_is_possibly_dangerous_unsafe_name():
    # Test that unsafe names are marked as dangerous
    unsafe_names = [
        "open",
        "input",
        "system",
        "eval",
        "exec",
        "compile",
        "import",
        "from",
        "global",
        "nonlocal",
        "lambda",
        "del",
        "pass",
        "assert",
        "raise",
        "try",
        "except",
        "finally",
        "with",
        "yield",
        "while",
        "for",
        "if",
        "else",
        "elif",
    ]
    for name in unsafe_names:
        assert token_is_possibly_dangerous(Token(type=token.NAME, string=name))
