"""
Still need to figure out what to put here lol
"""

import regex as re
from aikido_firewall.vulnerabilities.sql_injection.consts import (
    SQL_DANGEROUS_IN_STRING,
    COMMON_SQL_KEYWORDS,
    SQL_KEYWORDS,
    SQL_OPERATORS,
)
from aikido_firewall.helpers import escape_string_regexp

cached_regexes = {}


def userinput_contains_sqlsyntax(user_input, dialect):
    """
    This function is the first check in order to determine if a SQL injection is happening,
    If the user input contains the necessary characters or words for a SQL injection, this
    function returns true.
    """

    # e.g. SELECT * FROM table WHERE column = 'value' LIMIT 1
    # If a query parameter is ?LIMIT=1 it would be blocked
    # If the body contains "LIMIT" or "SELECT" it would be blocked
    # These are common SQL keywords and appear in almost any SQL query
    if user_input.upper() in COMMON_SQL_KEYWORDS:
        return False

    regex = cached_regexes.get(dialect.__class__.__name__)

    if not regex:
        regex = build_regex(dialect)
        cached_regexes[dialect.__class__.__name__] = regex

    return bool(regex.search(user_input))


def build_regex(dialect):
    """
    This function builds our regex that will test for sql syntax
    """
    match_strings = [
        gen_match_sql_keywords(dialect),
        gen_match_sql_operators(),
        gen_match_sql_functions(),
        gen_match_dangerous_strings(dialect),
    ]
    print("|".join(match_strings))
    return re.compile("|".join(match_strings), re.VERBOSE)


def gen_match_sql_keywords(dialect):
    """
    Generate the string which matches sql keywords (dialect included)
    """
    escaped_kw_with_dialect = map(
        escape_string_regexp, SQL_KEYWORDS + dialect.get_keywords()
    )
    match_sql_keywords = [
        # Lookbehind : if the keywords are preceded by one or more letters, it should not match
        r"(?<![a-z])(",
        # Look for SQL Keywords
        "|".join(escaped_kw_with_dialect),
        # Lookahead : if the keywords are followed by one or more letters, it should not match
        r")(?![a-z])",
    ]
    return "".join(match_sql_keywords)


def gen_match_sql_operators():
    """
    Generate the string which matches sql operators
    """
    return "(" + "|".join(map(re.escape, SQL_OPERATORS)) + ")"


def gen_match_sql_functions():
    """
    Generate the string which matches sql functions
    """
    match_sql_functions = [
        # Lookbehind : A sql function should be preceded by spaces, dots,
        r"(?<=([\s.",
        # Or sql operators
        "|".join(map(escape_string_regexp, SQL_OPERATORS)),
        r"]|^)+)",
        # The name of a sql function can include letters, numbers, "_" and "-"
        r"([a-z0-9_-]+)",
        # Lookahead : A sql function should be followed by a "(" , spaces are allowed.
        r"(?=[\s]*\()",
    ]
    return "".join(match_sql_functions)


def gen_match_dangerous_strings(dialect):
    """
    Generate the regex string which matches dangerous sql strings
    """
    dangerous_strings = SQL_DANGEROUS_IN_STRING + dialect.get_dangerous_strings()
    return "|".join(map(escape_string_regexp, dangerous_strings))
