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
    assert contains_shell_syntax("lsattr", "lsattr") is True


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


def test_detects_commands_with_separators():
    assert contains_shell_syntax("rm>arg", "rm") is True


def test_detects_commands_with_separators():
    assert contains_shell_syntax("rm<arg", "rm") is True


def test_empty_command_and_input():
    assert contains_shell_syntax("", "") is False
    assert contains_shell_syntax("", "rm") is False
    assert contains_shell_syntax("rm", "") is False


def test_command_with_special_characters():
    assert contains_shell_syntax("echo $HOME", "echo") is True
    assert contains_shell_syntax("echo $HOME", "$HOME") is True
    assert contains_shell_syntax('echo "Hello World"', "echo") is True
    assert contains_shell_syntax("echo 'Hello World'", "echo") is True


def test_command_with_multiple_separators():
    assert contains_shell_syntax("rm -rf; echo 'done'", "rm") is True
    assert contains_shell_syntax("ls | grep 'test'", "ls") is True
    assert contains_shell_syntax("find . -name '*.txt' | xargs rm", "rm") is True


def test_command_with_path_prefixes():
    assert contains_shell_syntax("/bin/rm -rf /tmp", "/bin/rm") is True
    assert (
        contains_shell_syntax("/usr/bin/killall process_name", "/usr/bin/killall")
        is True
    )
    assert contains_shell_syntax("/sbin/shutdown now", "/sbin/shutdown") is True


def test_command_with_colon():
    assert contains_shell_syntax(":; echo 'test'", ":") is True
    assert contains_shell_syntax("echo :; echo 'test'", ":") is True


def test_command_with_newline_separators():
    assert contains_shell_syntax("echo 'Hello'\nrm -rf /tmp", "rm") is True
    assert contains_shell_syntax("echo 'Hello'\n", "echo") is True


def test_command_with_tabs():
    assert contains_shell_syntax("echo 'Hello'\trm -rf /tmp", "rm") is True
    assert contains_shell_syntax("\techo 'Hello'", "echo") is True


def test_command_with_invalid_input():
    assert contains_shell_syntax("echo 'Hello'", "invalid_command") is False
    assert contains_shell_syntax("ls -l", "rm") is False


def test_command_with_multiple_commands():
    assert contains_shell_syntax("rm -rf; ls -l; echo 'done'", "ls") is True
    assert contains_shell_syntax("echo 'Hello'; rm -rf /tmp", "rm") is True


def test_command_with_no_separators():
    assert contains_shell_syntax("echoHello", "echo") is False
    assert contains_shell_syntax("rmrf", "rm") is False


def test_command_with_dangerous_chars():
    assert contains_shell_syntax("rm -rf; echo 'done'", ";") is True
    assert contains_shell_syntax("echo 'Hello' & rm -rf /tmp", "&") is True
    assert contains_shell_syntax("echo 'Hello' | rm -rf /tmp", "|") is True


def test_command_with_path_and_arguments():
    assert contains_shell_syntax("/usr/bin/ls -l", "/usr/bin/ls") is True
    assert contains_shell_syntax("/bin/cp file1 file2", "/bin/cp") is True
