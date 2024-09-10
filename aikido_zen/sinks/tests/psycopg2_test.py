import pytest
from unittest.mock import patch
import aikido_zen.sinks.psycopg2
from aikido_zen.background_process.comms import reset_comms
from aikido_zen.vulnerabilities.sql_injection.dialects import Postgres

kind = "sql_injection"
op = "pymysql.connections.query"


@pytest.fixture
def database_conn():
    import psycopg2

    return psycopg2.connect(
        host="127.0.0.1", user="user", password="password", database="db"
    )


def test_cursor_execute(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        query = "SELECT * FROM dogs"
        cursor.execute(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert isinstance(called_with_args[1], Postgres)
        mock_run_vulnerability_scan.assert_called_once()

        cursor.fetchall()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_execute_parameterized(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        query = "INSERT INTO dogs (dog_name, isadmin) VALUES (%s, %s)"
        cursor.execute(query, ("doggo", True))

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert isinstance(called_with_args[1], Postgres)
        mock_run_vulnerability_scan.assert_called_once()

        database_conn.commit()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_executemany(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        data = [
            ("Doggy", False),
            ("Doggy 2", True),
            ("Dogski", True),
        ]
        cursor.executemany("INSERT INTO dogs (dog_name, isadmin) VALUES (%s, %s)", data)
        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert (
            called_with_args[0]
            == "INSERT INTO dogs (dog_name, isadmin) VALUES (%s, %s)"
        )
        assert isinstance(called_with_args[1], Postgres)
        mock_run_vulnerability_scan.assert_called_once()

        database_conn.commit()
        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()
