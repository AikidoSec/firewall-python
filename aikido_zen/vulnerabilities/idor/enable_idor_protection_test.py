import pytest
from aikido_zen.storage.idor_protection_config import idor_protection_store
from .enable_idor_protection import enable_idor_protection


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    idor_protection_store.clear()


def test_enable_basic():
    enable_idor_protection("tenant_id")
    config = idor_protection_store.get()
    assert config is not None
    assert config.tenant_column_name == "tenant_id"
    assert config.excluded_tables == []


def test_enable_with_excluded_tables():
    enable_idor_protection("org_id", excluded_tables=["migrations", "sessions"])
    config = idor_protection_store.get()
    assert config is not None
    assert config.tenant_column_name == "org_id"
    assert config.excluded_tables == ["migrations", "sessions"]


def test_invalid_column_name_type(caplog):
    enable_idor_protection(123)
    assert idor_protection_store.get() is None
    assert "expects tenant_column_name to be a string" in caplog.text


def test_empty_column_name(caplog):
    enable_idor_protection("")
    assert idor_protection_store.get() is None
    assert "non-empty string" in caplog.text


def test_invalid_excluded_tables_type(caplog):
    enable_idor_protection("tenant_id", excluded_tables="not_a_list")
    assert idor_protection_store.get() is None
    assert "expects excluded_tables to be a list" in caplog.text


def test_invalid_excluded_table_item(caplog):
    enable_idor_protection("tenant_id", excluded_tables=[123])
    assert idor_protection_store.get() is None
    assert "expects excluded_tables to contain strings" in caplog.text


def test_none_column_name(caplog):
    enable_idor_protection(None)
    assert idor_protection_store.get() is None
    assert "expects tenant_column_name to be a string" in caplog.text
