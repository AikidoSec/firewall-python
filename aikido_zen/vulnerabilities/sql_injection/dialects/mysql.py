"""
File includes MySQL dialect
"""

from aikido_zen.vulnerabilities.sql_injection.dialects.abstract import SQLDialect


class SQLDialectMySQL(SQLDialect):
    """
    This is the MySQL dialect, it includes strings specific to MySQL
    """

    def get_dangerous_strings(self):
        return []

    def get_keywords(self):
        return [
            # https://dev.mysql.com/doc/refman/8.0/en/set-variable.html
            "GLOBAL",
            "SESSION",
            "PERSIST",
            "PERSIST_ONLY",
            "@@GLOBAL",
            "@@SESSION",
            # https://dev.mysql.com/doc/refman/8.0/en/set-character-set.html
            "CHARACTER SET",
            "CHARSET",
        ]
