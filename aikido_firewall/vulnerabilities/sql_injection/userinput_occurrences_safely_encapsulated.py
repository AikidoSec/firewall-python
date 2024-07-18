"""
????
"""

from aikido_firewall.helpers import get_current_and_next_segments
from aikido_firewall.vulnerabilities.sql_injection.consts import SQL_STRING_CHARS


# escape_sequences_regex define
def userinput_occurrences_safely_encapsulated(query, user_input):
    """
    ???
    """
    segments_in_between = get_current_and_next_segments(query.split(user_input))

    for segment in segments_in_between:
        current_segment = segment["currentSegment"]
        next_segment = segment["nextSegment"]

        input_str = user_input
        char_before_user_input = current_segment[-1]
        char_after_user_input = next_segment[0]
        quote_char = next(
            (char for char in SQL_STRING_CHARS if char == char_before_user_input), None
        )

        for char in ['"', "'"]:
            if (
                not quote_char
                and input_str.startswith(char)
                and current_segment[-2:] == f"{char}\\"
                and char_after_user_input == char
            ):
                quote_char = char
                char_before_user_input = current_segment[-2]
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
