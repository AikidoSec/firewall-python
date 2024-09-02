import pytest
from unittest.mock import patch
import aikido_firewall.sinks.mysqlclient
from aikido_firewall.background_process.comms import reset_comms
from aikido_firewall.vulnerabilities.sql_injection.dialects import MySQL

kind = "sql_injection"
op = "MySQLdb.connections.query"


@pytest.fixture
def database_conn():
    import MySQLdb

    return MySQLdb.connect(host="127.0.0.1", user="user", passwd="password", db="db")


def test_cursor_execute(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        query = "SELECT * FROM dogs"
        cursor.execute(query)
        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert isinstance(called_with_args[1], MySQL)

        mock_run_vulnerability_scan.assert_called_once()
        cursor.fetchall()
        mock_run_vulnerability_scan.assert_called_once()

        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_executemany(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
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
            == "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Doggy', 0),('Doggy 2', 1),('Dogski', 1)"
        )
        assert isinstance(called_with_args[1], MySQL)
        mock_run_vulnerability_scan.assert_called_once()
        database_conn.commit()
        mock_run_vulnerability_scan.assert_called_once()

        cursor.close()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_callproc(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        import MySQLdb

        cursor = database_conn.cursor()
        with pytest.raises(MySQLdb.OperationalError):
            cursor.callproc("test_procedure", (5, 10, 2))

        calls = mock_run_vulnerability_scan.call_args_list

        first_call_args = calls[0][1]["args"]
        assert (
            first_call_args[0]
            == "SET @_test_procedure_0=5,@_test_procedure_1=10,@_test_procedure_2=2"
        )
        assert isinstance(first_call_args[1], MySQL)

        second_call_args = calls[1][1]["args"]
        assert (
            second_call_args[0]
            == "CALL test_procedure(@_test_procedure_0,@_test_procedure_1,@_test_procedure_2)"
        )
        assert isinstance(second_call_args[1], MySQL)
        mock_run_vulnerability_scan.assert_called()

        database_conn.commit()
        cursor.close()
        database_conn.close()
