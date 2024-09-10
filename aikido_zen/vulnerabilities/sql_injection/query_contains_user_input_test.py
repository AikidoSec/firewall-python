"""
Test file for __init__.py
"""

# pylint: disable=unused-import
import pytest
from aikido_zen.vulnerabilities.sql_injection.query_contains_user_input import (
    query_contains_user_input,
)


class TestInitSqlInjection:
    """Testing class"""

    def test(self):
        """it checks if query contains user input"""
        assert query_contains_user_input("SELECT * FROM 'Jonas';", "Jonas")
        assert query_contains_user_input("Hi I'm MJoNaSs", "jonas")
        assert query_contains_user_input("Hiya, 123^&*( is a real string", "123^&*(")
        assert not query_contains_user_input("Roses are red", "violet")
