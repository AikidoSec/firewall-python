import pytest
from unittest.mock import patch
import aikido_firewall.sinks.asyncpg
from aikido_firewall.background_process.comms import reset_comms
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres

kind = "sql_injection"
op = "MySQLdb.connections.query"


@pytest.fixture
async def database_conn():
    import asyncpg

    conn = await asyncpg.connect(
        host="127.0.0.1", user="user", password="password", database="db"
    )
    return conn


@pytest.mark.asyncio
async def test_cursor_execute(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "SELECT * FROM dogs"
        await conn.execute(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert isinstance(called_with_args[1], Postgres)
        mock_run_vulnerability_scan.assert_called_once()

        await conn.close()
        mock_run_vulnerability_scan.assert_called_once()
