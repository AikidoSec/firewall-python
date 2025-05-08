import sys

import pytest
from unittest.mock import patch
import aikido_zen.sinks.psycopg2
from aikido_zen.background_process.comms import reset_comms

kind = "sql_injection"
op = "pymysql.connections.query"

# psycopg2 not working on python 3.13 for now
skip_python_3_13 = sys.version_info[:2] == (3, 13)


@pytest.fixture
def database_conn():
    import psycopg2
    from psycopg2.extras import DictCursor

    return psycopg2.connect(
        cursor_factory=DictCursor,
        host="127.0.0.1",
        user="user",
        password="password",
        database="db",
    )


@pytest.fixture
def database_conn_immutable_cursor():
    import psycopg2
    from psycopg2.extensions import cursor

    return psycopg2.connect(
        cursor_factory=cursor,
        host="127.0.0.1",
        user="user",
        password="password",
        database="db",
    )


@pytest.fixture
def database_conn_empty_cursor():
    import psycopg2

    return psycopg2.connect(
        host="127.0.0.1",
        user="user",
        password="password",
        database="db",
    )


@pytest.mark.skipif(skip_python_3_13, reason="Skipping test on Python 3.13")
def test_cursor_execute(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        print(cursor)
        query = "SELECT * FROM dogs"
        cursor.execute(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "postgres"
        mock_run_vulnerability_scan.assert_called_once()

        cursor.fetchall()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.skipif(skip_python_3_13, reason="Skipping test on Python 3.13")
def test_cursor_execute2(database_conn_empty_cursor):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn_empty_cursor.cursor()
        query = "SELECT * FROM dogs"
        cursor.execute(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "postgres"
        mock_run_vulnerability_scan.assert_called_once()

        cursor.fetchall()
        database_conn_empty_cursor.close()
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.skipif(skip_python_3_13, reason="Skipping test on Python 3.13")
def test_cursor_execute3(database_conn_immutable_cursor):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn_immutable_cursor.cursor()
        query = "SELECT * FROM dogs"
        cursor.execute(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "postgres"
        mock_run_vulnerability_scan.assert_called_once()

        cursor.fetchall()
        database_conn_immutable_cursor.close()
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.skipif(skip_python_3_13, reason="Skipping test on Python 3.13")
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
        assert called_with_args[1] == "postgres"
        database_conn.commit()
        database_conn.close()


@pytest.mark.skipif(skip_python_3_13, reason="Skipping test on Python 3.13")
def test_cursor_execute_parameterized2(database_conn_empty_cursor):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn_empty_cursor.cursor()
        query = "INSERT INTO dogs (dog_name, isadmin) VALUES (%s, %s)"
        cursor.execute(query, ("doggo", True))

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "postgres"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn_empty_cursor.commit()
        database_conn_empty_cursor.close()
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.skipif(skip_python_3_13, reason="Skipping test on Python 3.13")
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
        assert called_with_args[1] == "postgres"

        database_conn.commit()
        cursor.close()
        database_conn.close()


@pytest.mark.skipif(skip_python_3_13, reason="Skipping test on Python 3.13")
def test_cursor_executemany2(database_conn_empty_cursor):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn_empty_cursor.cursor()
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
        assert called_with_args[1] == "postgres"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn_empty_cursor.commit()
        cursor.close()
        database_conn_empty_cursor.close()
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.skipif(skip_python_3_13, reason="Skipping test on Python 3.13")
def test_cursor_executemany3(database_conn_immutable_cursor):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn_immutable_cursor.cursor()
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
        assert called_with_args[1] == "postgres"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn_immutable_cursor.commit()
        cursor.close()
        database_conn_immutable_cursor.close()
        mock_run_vulnerability_scan.assert_called_once()
