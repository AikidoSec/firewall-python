import pytest
from .attacks import attack_get_human_name


def test_attack_get_human_name_nosql_injection():
    assert attack_get_human_name("nosql_injection") == "a NoSQL injection"


def test_attack_get_human_name_sql_injection():
    assert attack_get_human_name("sql_injection") == "an SQL injection"


def test_attack_get_human_name_unknown_kind():
    assert attack_get_human_name("skjdg") == "Unknown attack kind"


def test_attack_get_human_name_unknown_kind():
    assert attack_get_human_name("fkpoewipowwpeo") == "Unknown attack kind"
