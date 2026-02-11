import pytest
from unittest.mock import patch
import aikido_zen.sinks.sqlite3
from aikido_zen.background_process.comms import reset_comms

kind = "sql_injection"


@pytest.fixture
def database_conn():
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE dogs (id INTEGER PRIMARY KEY, dog_name TEXT, isAdmin INTEGER)"
    )
    conn.commit()
    return conn


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
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        cursor.fetchall()
        mock_run_vulnerability_scan.assert_called_once()

        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_execute_parameterized(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        query = "INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)"
        cursor.execute(query, ("doggo", 0))

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn.commit()
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
        isadmin = 1
        query = f"INSERT INTO dogs (dog_name, isAdmin) VALUES ('{dogname}', {isadmin})"
        cursor.execute(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert (
            called_with_args[0]
            == "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Doggo', 1)"
        )
        assert called_with_args[1] == "sqlite"
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
        table_name = "dogs"
        value_2 = "1"
        cursor.execute(
            f"INSERT INTO {table_name} (dog_name, isAdmin) VALUES (?, {value_2})",
            ("doggy",),
        )

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert (
            called_with_args[0] == "INSERT INTO dogs (dog_name, isAdmin) VALUES (?, 1)"
        )
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn.commit()
        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_executemany(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        data = [
            ("Doggy", 0),
            ("Doggy 2", 1),
            ("Dogski", 1),
        ]
        cursor.executemany("INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", data)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert (
            called_with_args[0] == "INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)"
        )
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn.commit()
        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_executescript(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        script = """
            INSERT INTO dogs (dog_name, isAdmin) VALUES ('Fido', 0);
            INSERT INTO dogs (dog_name, isAdmin) VALUES ('Rex', 1);
        """
        cursor.executescript(script)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == script
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_connection_execute(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        query = "SELECT * FROM dogs"
        database_conn.execute(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_connection_execute_parameterized(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        query = "INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)"
        database_conn.execute(query, ("doggo", 0))

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn.commit()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_connection_executemany(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        data = [
            ("Doggy", 0),
            ("Doggy 2", 1),
            ("Dogski", 1),
        ]
        database_conn.executemany(
            "INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", data
        )

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert (
            called_with_args[0] == "INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)"
        )
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn.commit()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_connection_executescript(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        script = """
            INSERT INTO dogs (dog_name, isAdmin) VALUES ('Fido', 0);
            INSERT INTO dogs (dog_name, isAdmin) VALUES ('Rex', 1);
        """
        database_conn.executescript(script)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == script
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()
