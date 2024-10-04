import pytest
from unittest.mock import patch
import aikido_zen.sinks.asyncpg
import aikido_zen.sinks.os
from aikido_zen.background_process.comms import reset_comms

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
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "SELECT * FROM dogs"
        await conn.execute(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        called_with_op = mock_run_vulnerability_scan.call_args[1]["op"]
        called_with_kind = mock_run_vulnerability_scan.call_args[1]["kind"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "postgres"
        assert called_with_op == "asyncpg.connection.Connection.execute"
        assert called_with_kind == "sql_injection"

        await conn.close()


@pytest.mark.asyncio
async def test_conn_fetchrow(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "SELECT * FROM dogs"
        await conn.fetchrow(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "postgres"

        await conn.close()


@pytest.mark.asyncio
async def test_conn_fetch(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "SELECT * FROM dogs"
        await conn.fetch(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "postgres"

        await conn.close()


@pytest.mark.asyncio
async def test_conn_fetchval(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "SELECT COUNT(*) FROM dogs"
        await conn.fetchval(query)

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert called_with_args[0] == query
        assert called_with_args[1] == "postgres"

        await conn.close()


@pytest.mark.asyncio
async def test_conn_execute_parameterized(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        query = "INSERT INTO dogs(dog_name, isadmin) VALUES($1, $2)"
        await conn.execute(query, "Doggo", False)
        calls = mock_run_vulnerability_scan.call_args_list

        counter = 0
        for call in calls:
            args = call[1]["args"]
            if args[0] == query:
                counter += 1
        assert counter == 2

        await conn.close()


@pytest.mark.asyncio
async def test_conn_transaction(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        async with conn.transaction():
            query = "SELECT COUNT(*) FROM dogs"
            await conn.execute(query)

            calls = mock_run_vulnerability_scan.call_args_list
            begin_in_calls = False
            query_in_calls = False
            for call in calls:
                args = call[1]["args"]
                if args[0] == "BEGIN;":
                    begin_in_calls = True
                if args[0] == query:
                    query_in_calls = True
            assert begin_in_calls == query_in_calls == True

        await conn.close()


@pytest.mark.asyncio
async def test_conn_cursor(database_conn):
    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        conn = await database_conn
        async with conn.transaction():
            query = "SELECT COUNT(*) FROM dogs"
            await conn.cursor(query)

            calls = mock_run_vulnerability_scan.call_args_list

            called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
            assert called_with_args[0] == "BEGIN;"
            assert called_with_args[1] == "postgres"

        await conn.close()
