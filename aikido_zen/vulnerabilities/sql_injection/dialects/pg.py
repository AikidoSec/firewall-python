"""
File includes MySQL dialect
"""

from aikido_zen.vulnerabilities.sql_injection.dialects.abstract import SQLDialect


class SQLDialectPostgres(SQLDialect):
    """
    This is the Postgresql dialect, it includes strings specific to PG
    """

    def get_dangerous_strings(self):
        return [
            # https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-DOLLAR-QUOTING
            "$",
        ]

    def get_keywords(self):
        return [
            # https://www.postgresql.org/docs/current/sql-set.html
            "CLIENT_ENCODING",
        ]
