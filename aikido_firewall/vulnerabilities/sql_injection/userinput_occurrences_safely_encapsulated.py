"""
????
"""

import regex
from aikido_firewall.helpers.escape_string_regexp import escape_string_regexp
from aikido_firewall.helpers import get_current_and_next_segments
from aikido_firewall.vulnerabilities.sql_injection.consts import (
    SQL_STRING_CHARS,
    SQL_ESCAPE_SEQUENCES,
)

escape_sequences_pattern = regex.escape(
    "|".join(map(escape_string_regexp, SQL_ESCAPE_SEQUENCES))
)
escape_sequences_regex = regex.compile(escape_sequences_pattern, flags=regex.MULTILINE)


def userinput_occurrences_safely_encapsulated(query, user_input):
    """
    ???
    """
    segments_in_between = get_current_and_next_segments(query.split(user_input))

    for segment in segments_in_between:
        current_seg, next_seg = segment

        input_str = user_input
        char_before_user_input = current_seg[-1]
        char_after_user_input = next_seg[0]
        quote_char = next(
            (char for char in SQL_STRING_CHARS if char == char_before_user_input), None
        )

        # Special case for when the user input starts with a single quote
        # If the user input is `'value`
        # And the single quote is properly escaped with a backslash we split the following
        # `SELECT * FROM table WHERE column = '\'value'`
        # Into [`SELECT * FROM table WHERE column = '\`, `'`]
        # The char before the user input will be `\` and the char after the user input will be `'`
        for char in ['"', "'"]:
            if (
                not quote_char
                and input_str.startswith(char)
                and current_seg[-2:] == f"{char}\\"
                and char_after_user_input == char
            ):
                quote_char = char
                char_before_user_input = current_seg[-2]
                # Remove the escaped quote from the user input
                # otherwise we'll flag the user input as NOT safely encapsulated
                input_str = input_str[1:]
                break

        if not quote_char:
            return False

        if char_before_user_input != char_after_user_input:
            return False

        if char_before_user_input in input_str:
            return False

        without_escape_sequences = escape_sequences_regex.sub("", input_str)

        if "\\" in without_escape_sequences:
            return False

    return True
