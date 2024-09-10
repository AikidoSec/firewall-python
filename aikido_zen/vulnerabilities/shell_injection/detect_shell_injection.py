"""
Mainly exports detect_shell_injection function
"""

from .contains_shell_syntax import contains_shell_syntax
from .is_safely_encapsulated import is_safely_encapsulated


def detect_shell_injection(command, user_input):
    """
    Detects if there is a shell injection give user input
    and the command
    """
    # Block single ~ character. For example echo ~
    if user_input == "~":
        if len(command) > 1 and "~" in command:
            return True

    if len(user_input) <= 1:
        # We ignore single characters since they don't pose a big threat.
        # They are only able to crash the shell, not execute arbitrary commands.
        return False

    if len(user_input) > len(command):
        # We ignore cases where the user input is longer than the command.
        # Because the user input can't be part of the command.
        return False

    if user_input not in command:
        return False

    if is_safely_encapsulated(command, user_input):
        return False

    return contains_shell_syntax(command, user_input)
