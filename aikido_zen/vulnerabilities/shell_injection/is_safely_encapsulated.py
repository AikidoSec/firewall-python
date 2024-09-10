"""
Exports the is_safely_encapsulated function
"""

from aikido_zen.helpers.get_current_and_next_segments import (
    get_current_and_next_segments,
)

escape_chars = ['"', "'"]
dangerous_chars_inside_double_quotes = ["$", "`", "\\", "!"]


def is_safely_encapsulated(command, user_input):
    """Checks if the user input is safely encapsulated inside the command"""
    segments = get_current_and_next_segments(command.split(user_input))

    for segment in segments:
        current_segment = segment[0]
        next_segment = segment[1]

        char_before_user_input = current_segment[-1] if current_segment else None
        char_after_user_input = next_segment[0] if next_segment else None

        is_escape_char = char_before_user_input in escape_chars

        if not is_escape_char:
            return False

        if char_before_user_input != char_after_user_input:
            return False

        if char_before_user_input in user_input:
            return False

        #  There are no dangerous characters inside single quotes
        #  You can use certain characters inside double quotes
        #  https://www.gnu.org/software/bash/manual/html_node/Single-Quotes.html
        #  https://www.gnu.org/software/bash/manual/html_node/Double-Quotes.html
        if char_before_user_input == '"' and any(
            char in user_input for char in dangerous_chars_inside_double_quotes
        ):
            return False

    return True
