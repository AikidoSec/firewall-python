import pytest
from unittest.mock import patch
import aikido_zen.sinks.pymysql
from aikido_zen.background_process.comms import reset_comms
from aikido_zen.vulnerabilities.sql_injection.dialects import MySQL

kind = "sql_injection"
op = "pymysql.connections.query"


@pytest.fixture
def database_conn():
    import pymysql

    return pymysql.connect(host="127.0.0.1", user="user", passwd="password", db="db")


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
        assert isinstance(called_with_args[1], MySQL)
        mock_run_vulnerability_scan.assert_called_once()

        cursor.fetchall()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_execute_context(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        with database_conn.cursor() as cursor:
            query = "SELECT * FROM dogs"
            cursor.execute(query)

            called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
            assert called_with_args[0] == query
            assert isinstance(called_with_args[1], MySQL)
            mock_run_vulnerability_scan.assert_called_once()

            cursor.fetchall()
            database_conn.close()
            mock_run_vulnerability_scan.assert_called_once()


def test_cursor_execute_parameterized(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        with database_conn.cursor() as cursor:
            query = "INSERT INTO dogs (dog_name, isAdmin) VALUES (%s, %s)"
            cursor.execute(query, ("doggo", False))

            called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
            assert (
                called_with_args[0]
                == "INSERT INTO dogs (dog_name, isAdmin) VALUES (%s, %s)"
            )
            assert isinstance(called_with_args[1], MySQL)
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
        cursor.executemany("INSERT INTO dogs (dog_name, isAdmin) VALUES (%s, %s)", data)
        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert (
            called_with_args[0]
            == "INSERT INTO dogs (dog_name, isAdmin) VALUES (%s, %s)"
        )
        assert isinstance(called_with_args[1], MySQL)
        mock_run_vulnerability_scan.assert_called_once()
        database_conn.commit()
        mock_run_vulnerability_scan.assert_called_once()

        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_execute_with_fstring(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        data = ("doggy",)
        table_name = "dogs"
        value_2 = "1"
        cursor.execute(
            f"INSERT INTO {table_name} (dog_name, isAdmin) VALUES (%s, {value_2})", data
        )
        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert (
            called_with_args[0] == "INSERT INTO dogs (dog_name, isAdmin) VALUES (%s, 1)"
        )
        assert isinstance(called_with_args[1], MySQL)
        mock_run_vulnerability_scan.assert_called_once()
        database_conn.commit()
        mock_run_vulnerability_scan.assert_called_once()

        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_execute_no_args(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        dogname = "Doggo"
        isadmin = "TRUE"
        query = f'INSERT INTO dogs (dog_name, isAdmin) VALUES ("{dogname}", {isadmin})'
        cursor.execute(query)
        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert (
            called_with_args[0]
            == 'INSERT INTO dogs (dog_name, isAdmin) VALUES ("Doggo", TRUE)'
        )
        assert isinstance(called_with_args[1], MySQL)

        mock_run_vulnerability_scan.assert_called_once()
        cursor.fetchall()
        mock_run_vulnerability_scan.assert_called_once()

        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()
