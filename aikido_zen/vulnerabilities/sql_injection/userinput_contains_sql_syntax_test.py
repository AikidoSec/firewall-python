import os
import pytest
from aikido_zen.vulnerabilities.sql_injection.dialects import MySQL as DialectMySQL
from aikido_zen.vulnerabilities.sql_injection.dialects import Postgres as DialectPG
from aikido_zen.vulnerabilities.sql_injection.userinput_contains_sql_syntax import (
    userinput_contains_sqlsyntax,
)


def test_flags_dialect_specific_keywords():
    assert userinput_contains_sqlsyntax("@@GLOBAL", DialectMySQL()) == True


def test_does_not_flag_common_SQL_keywords():
    assert userinput_contains_sqlsyntax("SELECT", DialectMySQL()) == False


def file_paths():
    script_dir = os.path.dirname(__file__)
    return [
        # Taken from https://github.com/payloadbox/sql-injection-payload-list/tree/master
        os.path.join(script_dir, "payloads/Auth_Bypass.txt"),
        os.path.join(script_dir, "payloads/postgres.txt"),
        os.path.join(script_dir, "payloads/mysql.txt"),
        os.path.join(script_dir, "payloads/mssql_and_db2.txt"),
    ]


def test_flags_dangerous_SQL_syntax():
    for file_path in file_paths():
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                sql = line.rstrip("\n")
                assert userinput_contains_sqlsyntax(sql, DialectMySQL()) == True
                assert userinput_contains_sqlsyntax(sql, DialectPG()) == True


test_flags_dangerous_SQL_syntax()
