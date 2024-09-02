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
async def test_conn_execute(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "SELECT * FROM dogs"
        await conn.execute(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        called_with_op = mock_run_vulnerability_scan.call_args[1]["op"]
        called_with_kind = mock_run_vulnerability_scan.call_args[1]["kind"]
        assert called_with_args[0] == query
        assert isinstance(called_with_args[1], Postgres)
        mock_run_vulnerability_scan.assert_called_once()
        assert called_with_op == "asyncpg.connection.Connection.execute"
        assert called_with_kind == "sql_injection"

        await conn.close()
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_conn_fetchrow(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "SELECT * FROM dogs"
        await conn.fetchrow(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert isinstance(called_with_args[1], Postgres)
        mock_run_vulnerability_scan.assert_called_once()

        await conn.close()
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_conn_fetch(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "SELECT * FROM dogs"
        await conn.fetch(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert isinstance(called_with_args[1], Postgres)
        mock_run_vulnerability_scan.assert_called_once()

        await conn.close()
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_conn_fetchval(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "SELECT COUNT(*) FROM dogs"
        await conn.fetchval(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert isinstance(called_with_args[1], Postgres)
        mock_run_vulnerability_scan.assert_called_once()

        await conn.close()
        mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_conn_execute_parameterized(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "INSERT INTO dogs(dog_name, isadmin) VALUES($1, $2)"
        await conn.execute(query, "Doggo", False)
        calls = mock_run_vulnerability_scan.call_args_list

        first_call_args = calls[0][1]["args"]
        assert first_call_args[0] == query
        assert isinstance(first_call_args[1], Postgres)

        second_call_args = calls[1][1]["args"]
        assert second_call_args[0] == query
        assert isinstance(second_call_args[1], Postgres)

        await conn.close()


@pytest.mark.asyncio
async def test_conn_transaction(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        async with conn.transaction():
            query = "SELECT COUNT(*) FROM dogs"
            await conn.execute(query)

            calls = mock_run_vulnerability_scan.call_args_list

            first_call_args = calls[0][1]["args"]
            assert first_call_args[0] == "BEGIN;"
            assert isinstance(first_call_args[1], Postgres)

            second_call_args = calls[1][1]["args"]
            assert second_call_args[0] == query
            assert isinstance(second_call_args[1], Postgres)

        await conn.close()


@pytest.mark.asyncio
async def test_conn_cursor(database_conn):
    reset_comms()
    with patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        async with conn.transaction():
            query = "SELECT COUNT(*) FROM dogs"
            await conn.cursor(query)

            calls = mock_run_vulnerability_scan.call_args_list

            called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
            assert called_with_args[0] == "BEGIN;"
            assert isinstance(called_with_args[1], Postgres)
            mock_run_vulnerability_scan.assert_called_once()

        await conn.close()
