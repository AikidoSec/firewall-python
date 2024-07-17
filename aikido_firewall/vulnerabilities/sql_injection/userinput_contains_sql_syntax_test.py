import os
import pytest
from pathlib import Path
from aikido_firewall.vulnerabilities.sql_injection.dialects import MySQL as DialectMySQL
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres as DialectPG
from aikido_firewall.vulnerabilities.sql_injection.userinput_contains_sql_syntax import (
    userinput_contains_sqlsyntax,
)


def test_flags_dialect_specific_keywords():
    assert userinput_contains_sqlsyntax("@@GLOBAL", DialectMySQL()) == True


def test_does_not_flag_common_SQL_keywords():
    assert userinput_contains_sqlsyntax("SELECT", DialectMySQL()) == False


def test_flags_dangerous_SQL_syntax(path_files):
    for path_file in path_files:
        contents = path_file.read_text(encoding="utf-8")
        lines = contents.splitlines()
        for sql in lines:
            assert userinput_contains_sqlsyntax(sql, DialectMySQL()) == True
            assert userinput_contains_sqlsyntax(sql, DialectPG()) == True


@pytest.fixture
def path_files():
    return [
        # Taken from https://github.com/payloadbox/sql-injection-payload-list/tree/master
        Path(__file__).parent / "payloads" / "Auth_Bypass.txt",
        Path(__file__).parent / "payloads" / "postgres.txt",
        Path(__file__).parent / "payloads" / "mysql.txt",
        Path(__file__).parent / "payloads" / "mssql_and_db2.txt",
    ]
