"""Actual algorithm to detect code injection"""

import tokenize
from io import BytesIO
from .token_is_possibly_dangerous import token_is_possibly_dangerous


def detect_code_injection(statement, user_input):
    """
    Checks for code injection,
    - length smaller or equal to 3  : Ignore,
    - User input not in code : Ignore
    """
    if len(user_input) <= 3:
        # Don't run algorithm for small user input
        return False
    if user_input not in statement:
        # There cannot be an injection if user input is not present in the statement
        return False
    # Get the different counts, both with and without this user input :
    count_with_user_input = count_dangerous_tokens(statement)

    statement_without_user_input = statement.replace(user_input, "0")
    count_without_user_input = count_dangerous_tokens(statement_without_user_input)

    # If the count is not the same, this means non-safe python code was added because
    # of the user input, i.e. a code injection, return True
    is_injection = count_with_user_input != count_without_user_input
    return is_injection


def count_dangerous_tokens(statement):
    """Counts the amount of dangerous tokens resulting from the provided statement"""
    # Tokenize statement using python built-in tokenizer
    stream = BytesIO(statement.encode("utf-8")).readline
    tokens = tokenize.tokenize(stream)

    dangerous_tokens = list(filter(token_is_possibly_dangerous, tokens))

    # Return the amount of dangerous tokens :
    return len(dangerous_tokens)
