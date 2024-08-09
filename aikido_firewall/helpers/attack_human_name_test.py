import pytest
from .attack_human_name import attack_human_name


def test_nosql_injection():
    assert attack_human_name("nosql_injection") == "a NoSQL injection"


def test_sql_injection():
    assert attack_human_name("sql_injection") == "an SQL injection"


def test_shell_injection():
    assert attack_human_name("shell_injection") == "a shell injection"


def test_path_traversal():
    assert attack_human_name("path_traversal") == "a path traversal attack"


def test_ssrf():
    assert attack_human_name("ssrf") == "a server-side request forgery"


def test_unknown_attack():
    assert attack_human_name("unknown_attack") == "unknown"


def test_empty_string():
    assert attack_human_name("") == "unknown"


def test_none_input():
    assert attack_human_name(None) == "unknown"
