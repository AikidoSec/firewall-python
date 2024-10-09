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


def test_booleans_and_numbers():
    is_not_injection("True")
    is_not_injection("False")
    is_not_injection("0123456")
    is_not_injection("01234567.18234")
    is_not_injection("False True 012345.6789")


def test_maths_not_injection():
    is_not_injection("1 + 2 + 3 + 4 + 5")
    is_not_injection("1 + 2 + 3 + 4", "1 + 2 + 3")
    is_not_injection("1 - 2 + 3+4+5//20*200")
    is_not_injection("1 + 2 + (3 // 4)", "3 // 4")


def test_small_not_injection():
    is_not_injection("a.b")
    is_not_injection("abc")
    is_not_injection("abcdefghijklmnopabc", "abc")
    is_not_injection("def test_injection();", "();")


def test_not_in_userinput_not_injection():
    is_not_injection("def test_function(a=True, b=False):    pass", "test_function_not")
    is_not_injection("def test_injection();", "injection_none")


def test_injection_with_maths():
    is_injection("1 + 2 + (3 // 4)", "(3 // 4)")


def test_simple_injections():
    is_injection("os.system('ls')", "os.system('ls')")
    is_injection("exec('print(1)')", "exec('print(1)')")
    is_injection("eval('2 + 2')", "eval('2 + 2')")
    is_injection(
        "__import__('os').system('rm -rf /')", "__import__('os').system('rm -rf /')"
    )


def test_string_injections():
    is_injection("print('Hello, World!')")
    is_injection("input('Enter your name: ')")
    is_injection("os.system('rm -rf /');")


def test_nested_injections():
    is_injection("eval('print(1)')")
    is_injection("eval('os.system('ls')')")
    is_injection("exec('print(2)')")
    is_injection("exec('os.system('ls')')")


def test_edge_cases():
    is_injection("a = 1; b = 2")
    is_injection("b = 2; os.system('ls')")
    is_injection("def f(): pass")
    is_injection("f(); os.system('ls')")


def test_injection_with_special_characters():
    is_injection("print('Hello!')")
    is_injection("rm -rf /; #")
    is_injection("print('Goodbye!')")
    is_injection("echo 'Hacked!'; #")
