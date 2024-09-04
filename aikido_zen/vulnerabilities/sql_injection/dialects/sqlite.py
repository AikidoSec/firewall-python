"""
File includes SQLite dialect
"""

from aikido_zen.vulnerabilities.sql_injection.dialects.abstract import SQLDialect


class SQLDialectSQLite(SQLDialect):
    """
    This is the SQLite dialect, it includes strings specific to SQLite
    """

    def get_dangerous_strings(self):
        return []

    def get_keywords(self):
        return ["VACUUM", "ATTACH", "DETACH"]
