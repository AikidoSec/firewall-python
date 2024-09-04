import pytest
from .contains_shell_syntax import contains_shell_syntax


def test_detects_shell_syntax():
    assert contains_shell_syntax("", "") is False
    assert contains_shell_syntax("hello", "hello") is False
    assert contains_shell_syntax("\n", "\n") is False
    assert contains_shell_syntax("\n\n", "\n\n") is False

    assert contains_shell_syntax("$(command)", "$(command)") is True
    assert contains_shell_syntax("$(command arg arg)", "$(command arg arg)") is True
    assert contains_shell_syntax("`command`", "`command`") is True
    assert contains_shell_syntax("\narg", "\narg") is True
    assert contains_shell_syntax("\targ", "\targ") is True
    assert contains_shell_syntax("\narg\n", "\narg\n") is True
    assert contains_shell_syntax("arg\n", "arg\n") is True
    assert contains_shell_syntax("arg\narg", "arg\narg") is True
    assert contains_shell_syntax("rm -rf", "rm -rf") is True
    assert contains_shell_syntax("/bin/rm -rf", "/bin/rm -rf") is True
    assert contains_shell_syntax("/bin/rm", "/bin/rm") is True
    assert contains_shell_syntax("/sbin/sleep", "/sbin/sleep") is True
    assert contains_shell_syntax("/usr/bin/kill", "/usr/bin/kill") is True
    assert contains_shell_syntax("/usr/bin/killall", "/usr/bin/killall") is True
    assert contains_shell_syntax("/usr/bin/env", "/usr/bin/env") is True
    assert contains_shell_syntax("/bin/ps", "/bin/ps") is True
    assert contains_shell_syntax("/usr/bin/W", "/usr/bin/W") is True


def test_detects_commands_surrounded_by_separators():
    assert (
        contains_shell_syntax(
            r'find /path/to/search -type f -name "pattern" -exec rm {} \\;', "rm"
        )
        is True
    )


def test_detects_commands_with_separator_before():
    assert (
        contains_shell_syntax(
            'find /path/to/search -type f -name "pattern" | xargs rm', "rm"
        )
        is True
    )


def test_detects_commands_with_separator_after():
    assert contains_shell_syntax("rm arg", "rm") is True


def test_checks_if_same_command_occurs_in_user_input():
    assert contains_shell_syntax("find cp", "rm") is False


def test_treats_colon_as_command():
    assert contains_shell_syntax(":|echo", ":|") is True
    assert (
        contains_shell_syntax("https://www.google.com", "https://www.google.com")
        is False
    )
