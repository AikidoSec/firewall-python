"""
SQL Injection algorithm
"""

import re
import ctypes
from aikido_zen.helpers.logging import logger
from .map_dialect_to_rust_int import map_dialect_to_rust_int

zen_vulns_lib = ctypes.CDLL("zen_vulns_lib/libzen_rustlib.so")


def detect_sql_injection(query, user_input, dialect):
    """
    Execute this to check if the query is actually a SQL injection
    """
    if should_return_early(query, user_input):
        return False

    query_bytes = query.lower().encode("utf-8")
    userinput_bytes = user_input.lower().encode("utf-8")
    dialect_int = map_dialect_to_rust_int(dialect)
    c_int_res = zen_vulns_lib.detect_sql_injection(
        query_bytes, userinput_bytes, dialect_int
    )
    return bool(c_int_res)


def should_return_early(query, user_input):
    """
    Returns true if the detect_sql_injection algo should return early :
    - user_input is <= 1 char or user input larger than query
    - user_input not in query
    - user_input is alphanumerical
    - user_input is an array of integers
    """
    if len(user_input) <= 1 or len(query) < len(user_input):
        # User input too small or larger than query, returning
        return True

    # Lowercase :
    query_l = query.lower()
    user_input_l = user_input.lower()
    if user_input_l not in query_l:
        # User input not in query, returning
        return True

    if user_input_l.replace("_", "").isalnum():
        # User input is alphanumerical (with underscores), returning
        return True

    cleaned_input_for_list = user_input_l.replace(" ", "").replace(",", "")
    is_valid_comma_seperated_number_list = re.match(r"^\d+$", cleaned_input_for_list)
    if is_valid_comma_seperated_number_list:
        # E.g. 1, 24028, 828, 4, 1
        return True

    return False
