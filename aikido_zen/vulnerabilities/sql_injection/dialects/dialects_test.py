import aikido_zen.vulnerabilities.sql_injection.dialects as dialects
import pytest


@pytest.fixture
def test_dialects():
    return [dialects.MySQL(), dialects.Postgres(), dialects.SQLite()]


def test_unique(test_dialects):
    """
    Making sure that there are no duplicates in the
    get_keywords() or get_dangerous_strings() arrays
    """
    for dialect in test_dialects:
        dangerous_strings = dialect.get_dangerous_strings()
        set_dangerous_strings = set(dangerous_strings)
        assert len(set_dangerous_strings) == len(dangerous_strings)

        keywords = dialect.get_keywords()
        set_keywords = set(keywords)
        assert len(set_keywords) == len(keywords)


def test_no_empty_strings(test_dialects):
    """
    Making sure that everything in the get_keywords()
    or in the get_dangerous_strings() arrays has a length higher than zero
    """
    for dialect in test_dialects:
        dangerous_strings = dialect.get_dangerous_strings()
        for keyword in dangerous_strings:
            assert len(keyword) > 0

        keywords = dialect.get_keywords()
        for keyword in keywords:
            assert len(keyword) > 0
