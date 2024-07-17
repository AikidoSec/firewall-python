"""
Still need to figure out what to put here lol
"""

import re
from aikido_firewall.vulnerabilities.sql_injection.consts import (
    SQL_DANGEROUS_IN_STRING,
    COMMON_SQL_KEYWORDS,
    SQL_KEYWORDS,
    SQL_OPERATORS,
)
from aikido_firewall.helpers import escape_string_regexp


def userinput_contains_sqlsyntax(user_input, dialect):
    """
    Checks if the user input contains any SQL, dialect is provided
    so we can also check if the user input contains dialect-specific SQL
    """
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
    return re.compile("|".join(match_strings), re.I | re.M)


def gen_match_sql_keywords(dialect):
    """
    Generate the string which matches sql keywords (dialect included)
    """
    escaped_kw_with_dialect = map(
        escape_string_regexp, SQL_KEYWORDS + dialect.getKeywords()
    )
    match_sql_keywords = [
        # Lookbehind : if the keywords are preceded by one or more letters, it should not match
        "(?<![a-z])(",
        # Look for SQL Keywords
        "|".join(escaped_kw_with_dialect),
        # Lookahead : if the keywords are followed by one or more letters, it should not match
        ")(?![a-z])",
    ]
    return "".join(match_sql_keywords)


def gen_match_sql_operators():
    """
    Generate the string which matches sql operators
    """
    return "(" + "|".join(map(escape_string_regexp, SQL_OPERATORS)) + ")"


def gen_match_sql_functions():
    """
    Generate the string which matches sql functions
    """
    match_sql_functions = [
        # Lookbehind : A sql function should be preceded by spaces, dots,
        "(?<=([\\s|.|",
        # Or sql operators
        "|".join(map(escape_string_regexp, SQL_OPERATORS)),
        "]|^)+)",
        # The name of a sql function can include letters, numbers, "_" and "-"
        "([a-z0-9_-]+)",
        # Lookahead : A sql function should be followed by a "(" , spaces are allowed.
        "(?=[\\s]*\\()",
    ]
    return "".join(match_sql_functions)


def gen_match_dangerous_strings(dialect):
    """
    Generate the regex string which matches dangerous sql strings
    """
    dangerous_strings = SQL_DANGEROUS_IN_STRING + dialect.get_dangerous_strings()
    return "|".join(map(escape_string_regexp, dangerous_strings))
