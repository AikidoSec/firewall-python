import pytest
from aikido_zen.context import current_context, Context
from aikido_zen.errors import AikidoIDOR
from aikido_zen.storage.idor_protection_config import (
    IdorProtectionConfig,
    idor_protection_store,
)
from .check_idor import run_idor_check, _sql_cache


@pytest.fixture(autouse=True)
def run_around_tests():
    _sql_cache.clear()
    yield
    current_context.set(None)
    idor_protection_store.clear()
    _sql_cache.clear()


def _setup(tenant_id="1", idor_ignored=False, column="tenant_id", excluded=None):
    idor_protection_store.set(IdorProtectionConfig(column, excluded or []))
    wsgi_request = {
        "REQUEST_METHOD": "GET",
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "localhost:8080",
        "PATH_INFO": "/hello",
        "QUERY_STRING": "",
        "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": "198.51.100.23",
    }
    ctx = Context(req=wsgi_request, body=None, source="flask")
    ctx.tenant_id = tenant_id
    ctx.idor_ignored = idor_ignored
    ctx.set_as_current_context()
    return ctx


# === SELECT tests ===


def test_select_with_correct_tenant_literal():
    _setup(tenant_id="1")
    # Should not raise
    run_idor_check("SELECT * FROM users WHERE tenant_id = 1", "postgres")


def test_select_missing_tenant_filter():
    _setup(tenant_id="1")
    with pytest.raises(AikidoIDOR, match="missing a filter on column 'tenant_id'"):
        run_idor_check("SELECT * FROM users WHERE name = 'test'", "postgres")


def test_select_wrong_tenant_id():
    _setup(tenant_id="1")
    with pytest.raises(
        AikidoIDOR, match="filters 'tenant_id' with value '2'.*tenant ID is '1'"
    ):
        run_idor_check("SELECT * FROM users WHERE tenant_id = 2", "postgres")


def test_select_with_dollar_placeholder_correct():
    _setup(tenant_id="42")
    run_idor_check("SELECT * FROM users WHERE tenant_id = $1", "postgres", ["42"])


def test_select_with_dollar_placeholder_wrong():
    _setup(tenant_id="42")
    with pytest.raises(
        AikidoIDOR, match="filters 'tenant_id' with value '99'.*tenant ID is '42'"
    ):
        run_idor_check("SELECT * FROM users WHERE tenant_id = $1", "postgres", ["99"])


def test_select_with_question_mark_placeholder_correct():
    _setup(tenant_id="10")
    run_idor_check("SELECT * FROM users WHERE tenant_id = ?", "mysql", [10])


def test_select_with_question_mark_placeholder_wrong():
    _setup(tenant_id="10")
    with pytest.raises(
        AikidoIDOR, match="filters 'tenant_id' with value '20'.*tenant ID is '10'"
    ):
        run_idor_check("SELECT * FROM users WHERE tenant_id = ?", "mysql", [20])


# === INSERT tests ===


def test_insert_with_correct_tenant():
    _setup(tenant_id="1")
    run_idor_check("INSERT INTO users (name, tenant_id) VALUES ('test', 1)", "postgres")


def test_insert_missing_tenant_column():
    _setup(tenant_id="1")
    with pytest.raises(
        AikidoIDOR, match="INSERT on table 'users' is missing column 'tenant_id'"
    ):
        run_idor_check("INSERT INTO users (name) VALUES ('test')", "postgres")


def test_insert_wrong_tenant_id():
    _setup(tenant_id="1")
    with pytest.raises(
        AikidoIDOR,
        match="INSERT on table 'users' sets 'tenant_id' to '2'.*tenant ID is '1'",
    ):
        run_idor_check(
            "INSERT INTO users (name, tenant_id) VALUES ('test', 2)", "postgres"
        )


def test_insert_with_placeholder_correct():
    _setup(tenant_id="5")
    run_idor_check(
        "INSERT INTO users (name, tenant_id) VALUES (?, ?)", "mysql", ["test", 5]
    )


def test_insert_with_placeholder_wrong():
    _setup(tenant_id="5")
    with pytest.raises(
        AikidoIDOR, match="INSERT on table 'users' sets 'tenant_id' to '9'"
    ):
        run_idor_check(
            "INSERT INTO users (name, tenant_id) VALUES (?, ?)", "mysql", ["test", 9]
        )


def test_multi_row_insert_second_row_wrong():
    _setup(tenant_id="1")
    with pytest.raises(
        AikidoIDOR, match="INSERT on table 'users' sets 'tenant_id' to '2'"
    ):
        run_idor_check(
            "INSERT INTO users (name, tenant_id) VALUES ('a', 1), ('b', 2)",
            "postgres",
        )


# === UPDATE / DELETE tests ===


def test_update_with_correct_tenant():
    _setup(tenant_id="1")
    run_idor_check("UPDATE users SET name = 'test' WHERE tenant_id = 1", "postgres")


def test_update_missing_tenant_filter():
    _setup(tenant_id="1")
    with pytest.raises(AikidoIDOR, match="missing a filter on column 'tenant_id'"):
        run_idor_check("UPDATE users SET name = 'test' WHERE name = 'old'", "postgres")


def test_delete_with_correct_tenant():
    _setup(tenant_id="1")
    run_idor_check("DELETE FROM users WHERE tenant_id = 1", "postgres")


def test_delete_missing_tenant_filter():
    _setup(tenant_id="1")
    with pytest.raises(AikidoIDOR, match="missing a filter on column 'tenant_id'"):
        run_idor_check("DELETE FROM users WHERE name = 'test'", "postgres")


# === Guard / bypass tests ===


def test_no_config_does_nothing():
    idor_protection_store.clear()
    run_idor_check("SELECT * FROM users", "postgres")


def test_no_context_does_nothing():
    idor_protection_store.set(IdorProtectionConfig("tenant_id", []))
    current_context.set(None)
    run_idor_check("SELECT * FROM users", "postgres")


def test_idor_ignored_skips_check():
    _setup(tenant_id="1", idor_ignored=True)
    # Should not raise even though filter is missing
    run_idor_check("SELECT * FROM users WHERE name = 'test'", "postgres")


def test_no_tenant_id_skips_check():
    _setup(tenant_id=None)
    run_idor_check("SELECT * FROM users WHERE name = 'test'", "postgres")


def test_excluded_table():
    _setup(tenant_id="1", excluded=["sessions"])
    # sessions is excluded, should not raise
    run_idor_check("SELECT * FROM sessions WHERE name = 'test'", "postgres")


def test_percent_s_placeholder_skipped():
    _setup(tenant_id="1")
    # %s queries cause a parse error, should be skipped gracefully
    run_idor_check("SELECT * FROM users WHERE tenant_id = %s", "postgres", [1])


def test_non_string_query_skipped():
    _setup(tenant_id="1")
    run_idor_check(123, "postgres")


def test_table_qualified_filter_matches():
    _setup(tenant_id="1")
    run_idor_check("SELECT * FROM users WHERE users.tenant_id = 1", "postgres")


def test_dollar_placeholder_with_multiple_params():
    _setup(tenant_id="42")
    run_idor_check(
        "SELECT * FROM users WHERE name = $1 AND tenant_id = $2",
        "postgres",
        ["test", "42"],
    )


def test_dollar_placeholder_wrong_with_multiple_params():
    _setup(tenant_id="42")
    with pytest.raises(AikidoIDOR):
        run_idor_check(
            "SELECT * FROM users WHERE name = $1 AND tenant_id = $2",
            "postgres",
            ["test", "99"],
        )
