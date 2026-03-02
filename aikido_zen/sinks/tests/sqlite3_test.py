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


# Functional tests — verify sqlite3 behavior is not broken by patching


def test_cursor_execute_returns_results(database_conn):
    cursor = database_conn.cursor()
    cursor.execute("INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", ("Fido", 1))
    database_conn.commit()

    cursor.execute("SELECT * FROM dogs WHERE dog_name = ?", ("Fido",))
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][1] == "Fido"
    assert rows[0][2] == 1
    cursor.close()


def test_cursor_fetchone(database_conn):
    cursor = database_conn.cursor()
    cursor.execute("INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", ("Rex", 0))
    database_conn.commit()

    cursor.execute("SELECT * FROM dogs")
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == "Rex"
    cursor.close()


def test_cursor_fetchmany(database_conn):
    cursor = database_conn.cursor()
    data = [("Dog1", 0), ("Dog2", 1), ("Dog3", 0)]
    cursor.executemany("INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", data)
    database_conn.commit()

    cursor.execute("SELECT * FROM dogs")
    rows = cursor.fetchmany(2)
    assert len(rows) == 2
    cursor.close()


def test_cursor_rowcount(database_conn):
    cursor = database_conn.cursor()
    cursor.execute("INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", ("Buddy", 0))
    assert cursor.rowcount == 1
    cursor.close()


def test_cursor_lastrowid(database_conn):
    cursor = database_conn.cursor()
    cursor.execute("INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", ("Max", 0))
    assert cursor.lastrowid is not None
    assert cursor.lastrowid > 0
    cursor.close()


def test_cursor_description(database_conn):
    cursor = database_conn.cursor()
    cursor.execute("SELECT * FROM dogs")
    assert cursor.description is not None
    col_names = [col[0] for col in cursor.description]
    assert col_names == ["id", "dog_name", "isAdmin"]
    cursor.close()


def test_executemany_inserts_all_rows(database_conn):
    cursor = database_conn.cursor()
    data = [("Dog1", 0), ("Dog2", 1), ("Dog3", 0)]
    cursor.executemany("INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", data)
    database_conn.commit()

    cursor.execute("SELECT COUNT(*) FROM dogs")
    count = cursor.fetchone()[0]
    assert count == 3
    cursor.close()


def test_executescript_runs_all_statements(database_conn):
    cursor = database_conn.cursor()
    script = """
        INSERT INTO dogs (dog_name, isAdmin) VALUES ('Script1', 0);
        INSERT INTO dogs (dog_name, isAdmin) VALUES ('Script2', 1);
    """
    cursor.executescript(script)

    cursor.execute("SELECT COUNT(*) FROM dogs")
    count = cursor.fetchone()[0]
    assert count == 2
    cursor.close()


def test_connection_as_context_manager():
    import sqlite3

    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        conn.execute("INSERT INTO test (val) VALUES (?)", ("hello",))
        row = conn.execute("SELECT val FROM test").fetchone()
        assert row[0] == "hello"


def test_connect_with_custom_factory():
    import sqlite3

    class CustomConnection(sqlite3.Connection):
        def custom_method(self):
            return "custom"

    conn = sqlite3.connect(":memory:", factory=CustomConnection)
    assert isinstance(conn, CustomConnection)
    assert conn.custom_method() == "custom"

    # Verify cursor operations still work through a custom factory
    conn.execute("CREATE TABLE t (v TEXT)")
    conn.execute("INSERT INTO t VALUES (?)", ("x",))
    row = conn.execute("SELECT v FROM t").fetchone()
    assert row[0] == "x"
    conn.close()


def test_connect_with_keyword_database():
    import sqlite3

    conn = sqlite3.connect(database=":memory:")
    conn.execute("CREATE TABLE kw_test (id INTEGER PRIMARY KEY, val TEXT)")
    conn.execute("INSERT INTO kw_test (val) VALUES (?)", ("kw",))
    row = conn.execute("SELECT val FROM kw_test").fetchone()
    assert row[0] == "kw"
    conn.close()


def test_row_factory(database_conn):
    import sqlite3

    database_conn.row_factory = sqlite3.Row
    cursor = database_conn.cursor()
    cursor.execute("INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", ("RowFido", 1))
    database_conn.commit()

    cursor.execute("SELECT * FROM dogs WHERE dog_name = ?", ("RowFido",))
    row = cursor.fetchone()
    assert row["dog_name"] == "RowFido"
    assert row["isAdmin"] == 1
    cursor.close()


def test_cursor_with_custom_factory(database_conn):
    import sqlite3

    class CustomCursor(sqlite3.Cursor):
        pass

    reset_comms()
    with patch(
        "aikido_zen.vulnerabilities.run_vulnerability_scan"
    ) as mock_run_vulnerability_scan:
        cursor = database_conn.cursor(factory=CustomCursor)
        assert isinstance(cursor, CustomCursor)

        cursor.execute(
            "INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)", ("FactoryFido", 1)
        )
        database_conn.commit()

        called_with_args = mock_run_vulnerability_scan.call_args[1]["args"]
        assert (
            called_with_args[0] == "INSERT INTO dogs (dog_name, isAdmin) VALUES (?, ?)"
        )
        assert called_with_args[1] == "sqlite"
        mock_run_vulnerability_scan.assert_called_once()

        cursor.execute("SELECT * FROM dogs WHERE dog_name = ?", ("FactoryFido",))
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][1] == "FactoryFido"
        cursor.close()
