import pytest
from unittest.mock import patch

import pytest_asyncio

import aikido_zen.sinks.psycopg
from aikido_zen.background_process.ipc import IPCClient


@pytest.fixture
def database_conn():
    import psycopg

    return psycopg.connect(
        host="127.0.0.1", user="user", password="password", dbname="db"
    )


def test_cursor_execute(database_conn):
    IPCClient.reset()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor()
        query = "SELECT * FROM dogs"
        cursor.execute(query)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == query
        assert called_with["args"][1] == "postgres"
        assert called_with["op"] == "psycopg.Cursor.execute"
        assert called_with["kind"] == "sql_injection"
        mock_run_vulnerability_scan.assert_called_once()

        cursor.fetchall()
        database_conn.close()
        mock_run_vulnerability_scan.assert_called_once()


def test_cursor_execute_parameterized(database_conn):
    IPCClient.reset()
    cursor = database_conn.cursor()
    query = "SELECT * FROM dogs WHERE dog_name = %s"
    params = ("Fido",)
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor.execute(query, params)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == "SELECT * FROM dogs WHERE dog_name = %s"
        assert called_with["args"][1] == "postgres"
        assert called_with["op"] == "psycopg.Cursor.execute"
        assert called_with["kind"] == "sql_injection"
        mock_run_vulnerability_scan.assert_called_once()

    cursor.fetchall()
    database_conn.close()


def test_cursor_executemany(database_conn):
    IPCClient.reset()
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
        assert called_with["args"][1] == "postgres"
        assert called_with["op"] == "psycopg.Cursor.executemany"
        assert called_with["kind"] == "sql_injection"
        mock_run_vulnerability_scan.assert_called()

    database_conn.commit()
    database_conn.close()


def test_cursor_copy(database_conn):
    IPCClient.reset()
    cursor = database_conn.cursor()
    query = "COPY dogs FROM STDIN"

    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor.copy(query)

        called_with = mock_run_vulnerability_scan.call_args[1]
        assert called_with["args"][0] == query
        assert called_with["args"][1] == "postgres"
        assert called_with["op"] == "psycopg.Cursor.copy"
        assert called_with["kind"] == "sql_injection"
        mock_run_vulnerability_scan.assert_called_once()

    database_conn.close()


@pytest.mark.asyncio
async def test_async_cursor_execute():
    import psycopg

    IPCClient.reset()
    async with await psycopg.AsyncConnection.connect(
        host="127.0.0.1", user="user", password="password", dbname="db"
    ) as conn:
        async with conn.cursor() as cursor:
            with patch(
                "aikido_zen.vulnerabilities.run_vulnerability_scan"
            ) as mock_run_vulnerability_scan:
                query = "SELECT * FROM dogs"
                await cursor.execute(query)

                called_with = mock_run_vulnerability_scan.call_args[1]
                assert called_with["args"][0] == query
                assert called_with["args"][1] == "postgres"
                assert called_with["op"] == "psycopg.AsyncCursor.execute"
                assert called_with["kind"] == "sql_injection"
                mock_run_vulnerability_scan.assert_called_once()

                await cursor.fetchall()
                mock_run_vulnerability_scan.assert_called_once()


@pytest.mark.asyncio
async def test_async_cursor_execute_parameterized():
    import psycopg

    IPCClient.reset()
    query = "SELECT * FROM dogs WHERE dog_name = %s"
    params = ("Fido",)

    async with await psycopg.AsyncConnection.connect(
        host="127.0.0.1", user="user", password="password", dbname="db"
    ) as conn:
        async with conn.cursor() as cursor:
            with patch(
                "aikido_zen.vulnerabilities.run_vulnerability_scan"
            ) as mock_run_vulnerability_scan:
                await cursor.execute(query, params)

                called_with = mock_run_vulnerability_scan.call_args[1]
                assert (
                    called_with["args"][0] == "SELECT * FROM dogs WHERE dog_name = %s"
                )
                assert called_with["args"][1] == "postgres"
                assert called_with["op"] == "psycopg.AsyncCursor.execute"
                assert called_with["kind"] == "sql_injection"
                mock_run_vulnerability_scan.assert_called_once()

                await cursor.fetchall()


@pytest.mark.asyncio
async def test_async_cursor_executemany():
    import psycopg

    IPCClient.reset()
    query = "INSERT INTO dogs (dog_name, isadmin) VALUES (%s, %s)"
    params = [("doggo1", False), ("Rex", False), ("Buddy", True)]

    async with await psycopg.AsyncConnection.connect(
        host="127.0.0.1", user="user", password="password", dbname="db"
    ) as conn:
        async with conn.cursor() as cursor:
            with patch(
                "aikido_zen.vulnerabilities.run_vulnerability_scan"
            ) as mock_run_vulnerability_scan:
                await cursor.executemany(query, params)

                # Check the last call to run_vulnerability_scan
                called_with = mock_run_vulnerability_scan.call_args[1]
                assert (
                    called_with["args"][0]
                    == "INSERT INTO dogs (dog_name, isadmin) VALUES (%s, %s)"
                )
                assert called_with["args"][1] == "postgres"
                assert called_with["op"] == "psycopg.AsyncCursor.executemany"
                assert called_with["kind"] == "sql_injection"
                mock_run_vulnerability_scan.assert_called()

            await conn.commit()


@pytest.mark.asyncio
async def test_async_cursor_copy():
    import psycopg

    IPCClient.reset()
    query = "COPY dogs FROM STDIN"

    async with await psycopg.AsyncConnection.connect(
        host="127.0.0.1", user="user", password="password", dbname="db"
    ) as conn:
        async with conn.cursor() as cursor:
            with patch(
                "aikido_zen.vulnerabilities.run_vulnerability_scan"
            ) as mock_run_vulnerability_scan:
                cursor.copy(query)

                called_with = mock_run_vulnerability_scan.call_args[1]
                assert called_with["args"][0] == query
                assert called_with["args"][1] == "postgres"
                assert called_with["op"] == "psycopg.AsyncCursor.copy"
                assert called_with["kind"] == "sql_injection"
                mock_run_vulnerability_scan.assert_called_once()
