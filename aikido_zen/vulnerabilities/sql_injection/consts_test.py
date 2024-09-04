import pytest
from aikido_zen.vulnerabilities.sql_injection.consts import (
    SQL_DANGEROUS_IN_STRING,
    COMMON_SQL_KEYWORDS,
    SQL_ESCAPE_SEQUENCES,
    SQL_KEYWORDS,
    SQL_OPERATORS,
    SQL_STRING_CHARS,
)


def test_sql_keywords_not_empty():
    for keyword in SQL_KEYWORDS:
        assert len(keyword) > 0


def test_sql_keywords_uppercase():
    for keyword in SQL_KEYWORDS:
        assert keyword == keyword.upper()


def test_common_sql_keywords_not_empty():
    for keyword in COMMON_SQL_KEYWORDS:
        assert len(keyword) > 0


def test_common_sql_keywords_uppercase():
    for keyword in COMMON_SQL_KEYWORDS:
        assert keyword == keyword.upper()


def test_sql_operators_not_empty():
    for operator in SQL_OPERATORS:
        assert len(operator) > 0


def test_sql_string_chars_single_chars():
    for char in SQL_STRING_CHARS:
        assert len(char) == 1


def test_sql_dangerous_in_string_not_empty():
    for char in SQL_DANGEROUS_IN_STRING:
        assert len(char) > 0


def test_sql_escape_sequences_not_empty():
    for sequence in SQL_ESCAPE_SEQUENCES:
        assert len(sequence) > 0
