"""
Helper function file, see function doc for explanation
"""

import string

LOWERCASE = list(string.ascii_lowercase)
UPPERCASE = list(map(str.upper, LOWERCASE))
NUMBERS = list(string.digits)
SPECIAL = list("!#$%^&*|;:<>")
KNOWN_WORD_SEPARATORS = ["-"]
WHITE_SPACE = " "
MINIMUM_LENGTH = 10


def looks_like_a_secret(s):
    """
    This will make a judgement based on the string s wether
    or not s looks like a secret
    """
    if len(s) <= MINIMUM_LENGTH:
        return False

    has_number = any(char in s for char in NUMBERS)
    if not has_number:
        return False

    has_lower = any(char in s for char in LOWERCASE)
    has_upper = any(char in s for char in UPPERCASE)
    has_special = any(char in s for char in SPECIAL)
    charsets = [has_lower, has_upper, has_special]

    if charsets.count(True) < 2:
        return False

    if WHITE_SPACE in s:
        return False

    if any(separator in s for separator in KNOWN_WORD_SEPARATORS):
        return False

    window_size = MINIMUM_LENGTH
    ratios = []
    for i in range(len(s) - window_size + 1):
        window = s[i : i + window_size]
        unique_chars = set(window)
        ratios.append(len(unique_chars) / window_size)

    average_ratio = sum(ratios) / len(ratios)

    return average_ratio > 0.75
