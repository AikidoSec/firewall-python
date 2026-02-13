"""
SQL Injection algorithm
"""

import re
from aikido_zen.helpers.logging import logger
from .zen_internal_ffi import ZenInternal


def detect_sql_injection(query, user_input, dialect):
    """
    Execute this to check if the query is actually a SQL injection
    """
    try:
        query_l = query.lower()
        userinput_l = user_input.lower()
        if should_return_early(query_l, userinput_l):
            return False

        c_int_res = ZenInternal().detect_sql_injection(query_l, userinput_l, dialect)

        # This means that an error occurred in the library
        if c_int_res == 2:
            logger.debug(
                "Unable to check for SQL Injection, an error occurred in the library"
            )
            return False

        # This means that the library failed to tokenize the SQL query
        if c_int_res == 3:
            logger.debug("Unable to check for SQL Injection, SQL tokenization failed")
            return False

        return c_int_res == 1
    except Exception as e:
        logger.debug("Exception in SQL algo: %s", e)
    return False


def should_return_early(query, user_input):
    """
    Input : Lowercased query and user_input.
    Returns true if the detect_sql_injection algo should return early :
    - user_input is <= 1 char or user input larger than query
    - user_input not in query
    - user_input is alphanumerical
    - user_input is an array of integers
    """
    if len(user_input) <= 1 or len(query) < len(user_input):
        # User input too small or larger than query, returning
        return True

    if user_input not in query:
        # User input not in query, returning
        return True

    if user_input.replace("_", "").isalnum():
        # User input is alphanumerical (with underscores), returning
        return True

    cleaned_input_for_list = user_input.replace(" ", "").replace(",", "")
    is_valid_comma_seperated_number_list = re.match(r"^\d+$", cleaned_input_for_list)
    if is_valid_comma_seperated_number_list:
        # E.g. 1, 24028, 828, 4, 1
        return True

    return False
