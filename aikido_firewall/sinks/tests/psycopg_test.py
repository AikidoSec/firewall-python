import pytest
from unittest.mock import patch
import aikido_firewall.sinks.psycopg
from aikido_firewall.background_process.comms import reset_comms
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres

kind = "sql_injection"
op = "pymysql.connections.query"


@pytest.fixture
def database_conn():
    import psycopg

    return psycopg.connect(
        host="127.0.0.1", user="user", password="password", dbname="db"
    )


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
        assert isinstance(called_with_args[1], Postgres)
        mock_run_vulnerability_scan.assert_called_once()

        cursor.fetchall()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()
