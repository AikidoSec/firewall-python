"""
SQL Injection algorithm
"""

import re
import ctypes
from aikido_zen.helpers.logging import logger
from .map_dialect_to_rust_int import map_dialect_to_rust_int
from .get_lib_path import get_binary_path


def detect_sql_injection(query, user_input, dialect):
    """
    Execute this to check if the query is actually a SQL injection
    """
    try:
        query_l = query.lower()
        userinput_l = user_input.lower()
        if should_return_early(query_l, userinput_l):
            return False

        internals_lib = ctypes.CDLL(get_binary_path())
        query_bytes = query_l.encode("utf-8")
        userinput_bytes = userinput_l.encode("utf-8")
        dialect_int = map_dialect_to_rust_int(dialect)
        c_int_res = internals_lib.detect_sql_injection(
            query_bytes, userinput_bytes, dialect_int
        )

        # This means that an error occurred in the library
        if c_int_res == 2:
            logger.debug(
                "Unable to check for SQL Injection, an error occurred in the library"
            )
            return False

        return bool(c_int_res)
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
