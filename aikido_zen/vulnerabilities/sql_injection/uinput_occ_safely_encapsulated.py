"""
This module mainly provides the function uinput_occ_safely_encapsulated
"""

import regex as re
from aikido_zen.helpers.escape_string_regexp import escape_string_regexp
from aikido_zen.helpers import get_current_and_next_segments
from aikido_zen.vulnerabilities.sql_injection.consts import (
    SQL_STRING_CHARS,
    SQL_ESCAPE_SEQUENCES,
)

ESCAPE_SEQUENCES_PATTERN = "|".join(map(escape_string_regexp, SQL_ESCAPE_SEQUENCES))
escape_sequences_regex = re.compile(ESCAPE_SEQUENCES_PATTERN, re.M)


def js_slice(arr, start=None, end=None):
    """
    A more or less exact replica of the js slice function
    """
    length = len(arr)

    # Handle start index
    if start is None:
        start = 0
    elif start < 0:
        start = max(length + start, 0)
    else:
        start = min(start, length)

    # Handle end index
    if end is None:
        end = length
    elif end < 0:
        end = max(length + end, 0)
    else:
        end = min(end, length)

    # Perform slicing
    return arr[start:end]


def uinput_occ_safely_encapsulated(query, user_input):
    """
    This function will check if user input is actually just safely encapsulated in the query
    """
    segments_in_between = get_current_and_next_segments(
        query.lower().split(user_input.lower())
    )

    for segment in segments_in_between:
        current_seg, next_seg = segment

        input_str = user_input
        char_before_user_input = js_slice(current_seg, -1)
        char_after_user_input = js_slice(next_seg, 0, 1)
        quote_char = None
        for char in SQL_STRING_CHARS:
            if char == char_before_user_input:
                quote_char = char
                break

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
                and js_slice(current_seg, -2) == f"{char}\\"
                and char_after_user_input == char
            ):
                quote_char = char
                char_before_user_input = js_slice(current_seg, -2, -1)
                # Remove the escaped quote from the user input
                # otherwise we'll flag the user input as NOT safely encapsulated
                input_str = js_slice(input_str, 1)
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
