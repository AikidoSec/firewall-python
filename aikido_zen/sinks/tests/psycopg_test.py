import pytest
from unittest.mock import patch
import aikido_zen.sinks.psycopg
from aikido_zen.background_process.comms import reset_comms
from aikido_zen.vulnerabilities.sql_injection.dialects import Postgres


@pytest.fixture
def database_conn():
    import psycopg

    return psycopg.connect(
        host="127.0.0.1", user="user", password="password", dbname="db"
    )


def test_cursor_execute(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        query = "SELECT * FROM dogs"
        cursor.execute(query)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == query
        assert isinstance(called_with["args"][1], Postgres)
        assert called_with["op"] == "psycopg.Cursor.execute"
        assert called_with["kind"] == "sql_injection"
        mock_run_vulnerability_scan.assert_called_once()

        cursor.fetchall()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_execute_parameterized(database_conn):
    reset_comms()
    cursor = database_conn.cursor()
    query = "SELECT * FROM dogs WHERE dog_name = %s"
    params = ("Fido",)
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor.execute(query, params)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == "SELECT * FROM dogs WHERE dog_name = %s"
        assert isinstance(called_with["args"][1], Postgres)
        assert called_with["op"] == "psycopg.Cursor.execute"
        assert called_with["kind"] == "sql_injection"
        mock_run_vulnerability_scan.assert_called_once()

    cursor.fetchall()
    database_conn.close()


def test_cursor_executemany(database_conn):
    reset_comms()
    cursor = database_conn.cursor()
    query = "INSERT INTO dogs (dog_name, isadmin) VALUES (%s, %s)"
    params = [("doggo1", False), ("Rex", False), ("Buddy", True)]

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor.executemany(query, params)

        # Check the last call to run_vulnerability_scan
        called_with = mock_run_vulnerability_scan.call_args[1]
        assert (
            called_with["args"][0]
            == "INSERT INTO dogs (dog_name, isadmin) VALUES (%s, %s)"
        )
        assert isinstance(called_with["args"][1], Postgres)
        assert called_with["op"] == "psycopg.Cursor.executemany"
        assert called_with["kind"] == "sql_injection"
        mock_run_vulnerability_scan.assert_called()

    database_conn.commit()
    database_conn.close()


def test_cursor_copy(database_conn):
    reset_comms()
    cursor = database_conn.cursor()
    query = "COPY dogs FROM STDIN"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor.copy(query)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == query
        assert isinstance(called_with["args"][1], Postgres)
        assert called_with["op"] == "psycopg.Cursor.copy"
        assert called_with["kind"] == "sql_injection"
        mock_run_vulnerability_scan.assert_called_once()

    database_conn.close()
