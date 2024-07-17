"""
Test file for __init__.py
"""

# pylint: disable=unused-import
import pytest
import aikido_firewall.vulnerabilities.sql_injection as aik_sql


class TestInitSqlInjection:
    """Testing class"""

    def test(self):
        """it checks if query contains user input"""
        assert aik_sql.query_contains_user_input("SELECT * FROM 'Jonas';", "Jonas")
        assert aik_sql.query_contains_user_input("Hi I'm MJoNaSs", "jonas")
        assert aik_sql.query_contains_user_input(
            "Hiya, 123^&*( is a real string", "123^&*("
        )
        assert not aik_sql.query_contains_user_input("Roses are red", "violet")
