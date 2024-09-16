import pytest
from .detect_code_injection import detect_code_injection


def is_injection(statement, user_input=None):
    if user_input == None:
        assert detect_code_injection(statement, statement) is True
    else:
        assert detect_code_injection(statement, user_input) is True


def is_not_injection(statement, user_input=None):
    if user_input == None:
        assert detect_code_injection(statement, statement) is False
    else:
        assert detect_code_injection(statement, user_input) is False


def test_not_dangerous_comments():
    is_not_injection("# Hello! This (Might) Be Dangerous")
    is_not_injection(
        """# Well hello
    # Hello there !"""
    )
    is_not_injection(' """Hello again!"""  ')


def test_newline_and_indent_not_dangerous():
    is_not_injection("\n\n\n\n\n\n\n\n")
    is_not_injection("\r\n\r\n\r\n")
    is_not_injection("              ")
    is_not_injection("  ")
    is_not_injection("  \r\n    \n      \n  \t")
