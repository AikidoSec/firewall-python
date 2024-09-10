"""
Helper function file, see funtion definition
"""

import re


def escape_string_regexp(string):
    """
    Escape characters with special meaning either inside or outside character sets.
    Use a simple backslash escape when it's always valid, and a '\\xnn' escape
    when the simpler form would be disallowed by Unicode patterns' stricter grammar.
    Taken from https://github.com/sindresorhus/escape-string-regexp/
    """
    pattern = re.compile(r"[|\\{}()[\]^$+*?.]")
    replace1 = re.sub(pattern, r"\\\g<0>", string)
    return re.sub(r"-", r"\\x2d", replace1)
