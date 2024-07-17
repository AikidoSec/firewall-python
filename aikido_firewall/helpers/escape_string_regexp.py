"""
Helper function file, see funtion definition
"""

import re


def escape_string_regexp(string):
    """
    Escape characters with special meaning either inside or outside character sets.
    Use a simple backslash escape when it's always valid, and a '\\xnn' escape when the simpler form would be disallowed by Unicode patterns' stricter grammar.
    Taken from https://github.com/sindresorhus/escape-string-regexp/
    """
    return re.sub(r"[|\\{}()[\]^$+*?.]", r"\\\g<0>", "\\$&").replace("-", "\\x2d")
